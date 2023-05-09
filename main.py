import heapq
import queue
import sys
import curses
from time import time_ns
from resource import getrusage, RUSAGE_SELF

OPTIONS_NUM = 6

MINCOST_MINTIME_MODE = 0
MINCOST_MODE = 1
MINSTATIONSNUM_MODE = 2
LIMITCOST_MODE = 3
LIMITTIME_MODE = 4
WANT_TO_EXIT = 5

all_transport = [] # все виды транспорта
city_ind = {} # city -> ind
ind_city = {} # ind -> city
trans_ind = {} # transport_type -> ind
ind_trans = {} # ind -> transport_type

def get_time():
    return time_ns()
def get_mem():
    return getrusage(RUSAGE_SELF).ru_maxrss

class Edge:
    def __init__(self, from_city, to_city, transport_type, cruise_time, cruise_fare):
        # тут передаются идентификаторы
        self.from_city = from_city
        self.to_city = to_city
        self.transport_type = transport_type
        self.cruise_time = cruise_time
        self.cruise_fare = cruise_fare


class Path:
    def __init__(self):
        self.path = []

    def __getitem__(self, index):
        return self.path[index]

    def __add__(self, edge):
        new_path = Path()
        new_path.path = self.path + [edge]
        return new_path

    # def get_total_time(self):
    #     return sum([edge.get("time", 2**32) for edge in self.path])

    # def get_total_fare(self):
    #     return sum([edge.get("fare", 2**32) for edge in self.path])
    def add_begin(self, edge):
        self.path.insert(0, edge)
    def __str__(self):
        str_route = []
        for r in self.path:
            str_route.append(f"{ind_city[r.from_city]} -> {ind_city[r.to_city] }, time: {r.cruise_time}; fare: {r.cruise_fare}")
        return '\n'.join(str_route)


class Graph:
    def __init__(self):
        #словарь город: [рейсы]
        self.graph = {}
    def add_node(self, node: Edge):
        if node.from_city not in self.graph:
            self.graph[node.from_city] = []
        self.graph[node.from_city].append(node)
    def get_cruises(self, city_id):
        return self.graph[city_id]   


def parse_line(split_line: list) -> list:
    values = []
    buffer = []
    for value in split_line:
        try:
            if '"' == value[0] == value[-1]:
                values.append(value.replace('"', ''))
            elif '"' == value[0] != value[-1]:
                buffer.append(value)
            elif '"' == value[-1]:
                values.append(f'{buffer.pop()} {value}'.replace('"', ''))
            elif '\n' == value[-1]:
                values.append(int(value[:-1]))
            else:
                values.append(int(value))
        except ValueError:
            break
    return values


def parse_file(file_path: str):
    edges = []
    id = 0
    id_t = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            if line[0] == "#" or len(line) == 1:
                continue
            split_line = line.split(" ")
            from_city, to_city, transport_type, cruise_time, cruise_fare = parse_line(split_line)
            if transport_type not in trans_ind:
                trans_ind[transport_type] = id_t
                ind_trans[id_t] = transport_type
                id_t += 1 
            for city in [from_city, to_city]:    
                if city not in city_ind: 
                    city_ind[city] = id
                    ind_city[id] = city
                    id += 1
            edges.append(Edge(
                from_city=city_ind[from_city],
                to_city=city_ind[to_city],
                transport_type=trans_ind[transport_type],
                cruise_time=cruise_time,
                cruise_fare=cruise_fare
            ))
            if trans_ind[transport_type] not in all_transport:
                all_transport.append(trans_ind[transport_type])
    return edges


def bfs(graph: Graph, start: int, end: int, prohibited_transport: set):
    start = city_ind[start]
    end = city_ind[end]
    
    opt_dist = {vertex: 2**32 for vertex in graph.graph}
    visited = {}

    q = queue.Queue()
    q.put(start)
    
    opt_dist[start] = 0
    
    while not q.empty():
        current_vertex = q.get()
        for cruise in graph.get_cruises(current_vertex):
            if cruise.transport_type in prohibited_transport:
                continue
            elif opt_dist[cruise.to_city] == 2**32:
                q.put(cruise.to_city)
                opt_dist[cruise.to_city] = opt_dist[current_vertex] + 1
                visited[cruise.to_city] = cruise

    if end not in visited:
        return -1

    path = Path()
    act = end
    while act != start:
        path.add_begin(visited[act])
        act = visited[act].from_city
    return path


def calc_dijkstra_time(graph: Graph, start: int, prohibited_transport: set):
    #ind:расстояние
    opt_dist = {vertex: 2**32 for vertex in graph.graph}
    #ind:Edge
    visited = {}
    opt_dist[start] = 0
    pq = [(0, start)]
    while len(pq):
            current_time, current_vertex = heapq.heappop(pq)
            if current_time > opt_dist[current_vertex]:
                continue
            for cruise in graph.get_cruises(current_vertex):
                # если транспорт запрещен, то нам такой путь не нужен
                if cruise.transport_type in prohibited_transport:
                    continue
                distance = current_time + cruise.cruise_time
                if distance < opt_dist[cruise.to_city]:
                    opt_dist[cruise.to_city] = distance
                    visited[cruise.to_city] = cruise
                    heapq.heappush(pq, (distance, cruise.to_city))
    return (opt_dist, visited)


def restore_route_time(opt_dist, visited, from_city, to_city, lim_time = 2**32):
        if to_city not in visited:
            return -1
        #гарантия того, что мы там были + чек на время
        if opt_dist[to_city] >= lim_time:
            return -1
        path = Path()
        act = to_city
        while act != from_city:
            path.add_begin(visited[act])
            act = visited[act].from_city
        return path


def calc_dijkstra_cost(graph: Graph, start: int, prohibited_transport: set):
    #ind:расстояние
    opt_dist = {vertex: 2**32 for vertex in graph.graph}
    #ind:Edge
    visited = {}
    opt_dist[start] = 0
    pq = [(0, start)]
    while len(pq):
            current_fare, current_vertex = heapq.heappop(pq)
            if current_fare > opt_dist[current_vertex]:
                continue
            for cruise in graph.get_cruises(current_vertex):
                # если транспорт запрещен, то нам такой путь не нужен
                if cruise.transport_type in prohibited_transport:
                    continue
                distance = current_fare + cruise.cruise_fare
                if distance < opt_dist[cruise.to_city]:
                    opt_dist[cruise.to_city] = distance
                    visited[cruise.to_city] = cruise
                    heapq.heappush(pq, (distance, cruise.to_city))
    return (opt_dist, visited)


def restore_route_cost(opt_dist, visited, from_city, to_city, lim_cost = 2**32):
        if to_city not in visited:
            return -1
        #гарантия того, что мы там были + чек на время
        if opt_dist[to_city] >= lim_cost:
            return -1
        path = Path()
        act = to_city
        while act != from_city:
            path.add_begin(visited[act])
            act = visited[act].from_city
        return path


def calc_dijkstra_task1(graph: Graph, start: int, prohibited_transport: set):
    """среди быстрых самый дешевый """
    #ind:расстояние
    opt_dist = {vertex: 2**64 for vertex in graph.graph}
    #ind:Edge
    visited = {}
    opt_dist[start] = 0
    pq = [(0, start)]
    while len(pq):
            current_dist, current_vertex = heapq.heappop(pq)
            if current_dist > opt_dist[current_vertex]:
                continue
            for cruise in graph.get_cruises(current_vertex):
                # если транспорт запрещен, то нам такой путь не нужен
                if cruise.transport_type in prohibited_transport:
                    continue
                # умножаем cruise_time*2^32 + cruise_fare 
                distance = current_dist + (cruise.cruise_time<<32 | cruise.cruise_fare)
                if distance < opt_dist[cruise.to_city]:
                    opt_dist[cruise.to_city] = distance
                    visited[cruise.to_city] = cruise
                    heapq.heappush(pq, (distance, cruise.to_city))
    return (opt_dist, visited)


def restore_route_task1 (opt_dist, visited, from_city, to_city):
        if to_city not in visited:
            return -1
        #гарантия того, что мы там были + чек на время
        if opt_dist[to_city] >= 2**64:
            return -1
        path = Path()
        act = to_city
        while act != from_city:
            path.add_begin(visited[act])
            act = visited[act].from_city
        return path


def dijkstra_pq(graph: Graph, start: str, end: str, prohibited_transport: set, kind: str, lim = 0):
    """
    в зависимости что от нас требуется, kind это fare или time
    ну и лимиткост в зависимости какой, но вычисления одинаковые
    """
    start = city_ind[start]
    if end:
        end = city_ind[end]

    if kind == 'time':
        opt_dist, visited = calc_dijkstra_time(graph, start, prohibited_transport)
        #если ограничений нет, то один путь
        if lim == 0:
            return restore_route_time(opt_dist, visited, start, end)
        allowed_citys = []
        for vertex in visited:  
            if opt_dist[vertex] <= lim:
                allowed_citys.append(restore_route_time(opt_dist, visited, start, vertex))
        return allowed_citys
    elif kind == 'fare':
        opt_dist, visited = calc_dijkstra_cost(graph, start, prohibited_transport)
        #если ограничений нет, то один путь
        if lim == 0:
            return restore_route_cost(opt_dist, visited, start, end)
        allowed_citys = []
        for vertex in visited:  
            if opt_dist[vertex] <= lim:
                allowed_citys.append(restore_route_cost(opt_dist, visited, start, vertex))
        return allowed_citys
    else:
        opt_dist, visited = calc_dijkstra_task1(graph, start, prohibited_transport)
        return restore_route_task1(opt_dist, visited, start, end )

def main(stdscr):
    edges = parse_file(sys.argv[1])
    g = Graph()
    for edge in edges:
        g.add_node(edge)
    want_to_exit = False

    stdscr.scrollok(True)
    stdscr.keypad(True)

    while not want_to_exit:

        current_item_index = 0
        choice_made = False

        curses.noecho()

        choices = ["1). Нахождение пути минимальной стоимости среди кратчайших путей между двумя городами",
           "2). Нахождение пути минимальной стоимости между двумя городами",
           "3). Нахождение пути между двумя городами с минимальным числом пересадок",
           "4). Нахождение городов, достижимых из города отправления не более чем за лимит стоимости, и путей к ним",
           "5). Нахождение городов, достижимых из города отправления не более чем за лимит времени, и путей к ним",
           "Выйти из программы"]

        while not choice_made:
            stdscr.clear()
            curses.curs_set(0)
            stdscr.addstr("Выберите желаемый режим работы программы:\n\n")
            stdscr.refresh()

            for i in range(OPTIONS_NUM):
                if i == current_item_index:
                    stdscr.attron(curses.A_STANDOUT)
                    stdscr.addstr(f"{choices[i]}\n")
                    stdscr.attroff(curses.A_STANDOUT)
                else:
                    stdscr.addstr(f"{choices[i]}\n")
                stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_UP:
                if current_item_index > 0:
                    current_item_index -= 1
                else:
                    current_item_index = OPTIONS_NUM - 1
            elif key == curses.KEY_DOWN:
                if current_item_index < OPTIONS_NUM - 1:
                    current_item_index += 1
                else:
                    current_item_index = 0
            elif key == curses.KEY_ENTER or key == 10 or key == 13:
                choice_made = True

        if current_item_index >= 0 and current_item_index <= OPTIONS_NUM - 2:
            flag_0 = False
            was_transport_error = False
            while flag_0 == False:
                stdscr.clear()
                if was_transport_error:
                    stdscr.addstr(f"Транспорта вида {transport_type} нет, повторите ввод\n")
                was_transport_error = False
                stdscr.addstr("Введите запрещенные виды транспорта (через пробел). Если хотите разрешить все виды транспорта, то просто нажмите ENTER:\n\n")
                stdscr.refresh()
                curses.curs_set(1)
                curses.echo()

                prohibited_transport = str(stdscr.getstr(), "utf-8", errors="ignore")                        
                prohibited_transport = prohibited_transport.split(" ")
                if prohibited_transport == [""]:
                    prohibited_transport = set()
                    flag_0 = True
                else:
                    for transport_type in prohibited_transport:
                        if transport_type not in trans_ind:
                            was_transport_error = True
                            break
                    if not was_transport_error:
                        flag_0 = True
                        prohibited_transport = {trans_ind[trans_name] for trans_name in prohibited_transport}

        curses.echo()

        if current_item_index == MINCOST_MINTIME_MODE:
            flag_1 = False
            was_start_city_error = False
            while flag_1 == False:
                stdscr.clear()
                if was_start_city_error:
                    stdscr.addstr("Такого города нет, введите другой город отправления\n")
                stdscr.addstr("Введите город отправления:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                start_city = str(stdscr.getstr(), "utf-8", errors="ignore")                        
                if start_city not in city_ind:
                    was_start_city_error = True
                else:
                    flag_1 = True
                    was_start_city_error = False

            flag_2 = False
            was_exit_city_error = False
            while flag_2 == False:
                stdscr.clear()
                if was_exit_city_error:
                    stdscr.addstr("Такого города нет, введите другой город прибытия\n")
                stdscr.addstr("Введите город прибытия:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                exit_city = str(stdscr.getstr(), "utf-8", errors="ignore")                        
                if exit_city not in city_ind:
                    was_exit_city_error = True
                else:
                    flag_2 = True
                    was_exit_city_error = False

            #Запуск первого алгоритма
            time_work = get_time() 
            result = dijkstra_pq(g, start_city, exit_city, prohibited_transport, 'task1')
            time_work = get_time() - time_work 
            stdscr.clear()
            if result == -1:
                stdscr.addstr("Нет пути между выбранными городами c использованием указанных доступных видов транспорта\n")
                stdscr.addstr(f"время{time_work/10**9} сек, память:{get_mem()}\n")                
            else:
                #stdscr.addstr(f"Путь минимальной стоимости для 1 алго, используя доступные виды транспорта: {result[0]}\n")
                #stdscr.addstr(f"Минимальная стоимость: для первого алго {result[1]}\n")
                stdscr.addstr(f"{result}\n")
                stdscr.addstr(f"время{time_work/10**9} сек, память:{get_mem()}\n")
            stdscr.addstr("Нажмите любую клавишу для перехода в меню\n")
            stdscr.refresh()
            curses.curs_set(0)
            stdscr.getch()
                
        elif current_item_index == MINCOST_MODE:
            flag_1 = False
            was_start_city_error = False
            while flag_1 == False:
                stdscr.clear()
                if was_start_city_error:
                    stdscr.addstr("Такого города нет, введите другой город отправления\n")
                stdscr.addstr("Введите город отправления:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                start_city = str(stdscr.getstr(), "utf-8", errors="ignore")                        
                if start_city not in city_ind:
                    was_start_city_error = True
                else:
                    flag_1 = True
                    was_start_city_error = False

            flag_2 = False
            was_exit_city_error = False
            while flag_2 == False:
                stdscr.clear()
                if was_exit_city_error:
                    stdscr.addstr("Такого города нет, введите другой город прибытия\n")
                stdscr.addstr("Введите город прибытия:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                exit_city = str(stdscr.getstr(), "utf-8", errors="ignore")                        
                if exit_city not in city_ind:
                    was_exit_city_error = True
                else:
                    flag_2 = True
                    was_exit_city_error = False

            #Запуск второго алгоритма
            time_work = get_time()
            result = dijkstra_pq(g, start_city, exit_city, prohibited_transport, 'fare')
            time_work = get_time() - time_work
            stdscr.clear()
            if result == -1:
                stdscr.addstr("Нет пути между выбранными городами c использованием указанных доступных видов транспорта\n")
                stdscr.addstr(f"время{time_work/10**9} сек, память:{get_mem()}\n")
            else:
                #stdscr.addstr(f"Путь минимальной стоимости, используя доступные виды транспорта: {result[0]}\n")
                #stdscr.addstr(f"Минимальная стоимость: {result[1]}\n")
                stdscr.addstr(f"{result}\n")
                stdscr.addstr(f"время{time_work/10**9} сек, память:{get_mem()}\n")
            stdscr.addstr("Нажмите любую клавишу для перехода в меню\n")
            stdscr.refresh()
            curses.curs_set(0)
            stdscr.getch()

        elif current_item_index == MINSTATIONSNUM_MODE:
            flag_1 = False
            was_start_city_error = False
            while flag_1 == False:
                stdscr.clear()
                if was_start_city_error:
                    stdscr.addstr("Такого города нет, введите другой город отправления\n")
                stdscr.addstr("Введите город отправления:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                start_city = str(stdscr.getstr(), "utf-8", errors="ignore")                        
                if start_city not in city_ind:
                    was_start_city_error = True
                else:
                    flag_1 = True
                    was_start_city_error = False

            flag_2 = False
            was_exit_city_error = False
            while flag_2 == False:
                stdscr.clear()
                if was_exit_city_error:
                    stdscr.addstr("Такого города нет, введите другой город прибытия\n")
                stdscr.addstr("Введите город прибытия:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                exit_city = str(stdscr.getstr(), "utf-8", errors="ignore")                        
                if exit_city not in city_ind:
                    was_exit_city_error = True
                else:
                    flag_2 = True
                    was_exit_city_error = False

            #Запуск третьего алгоритма
            time_work = get_time()
            result = bfs(g, start_city, exit_city, prohibited_transport)
            time_work = get_time() - time_work
            stdscr.clear()
            if result == -1:
                stdscr.addstr("Нет пути между выбранными городами c использованием указанных доступных видов транспорта\n")
                stdscr.addstr(f"время{time_work/10**9} сек, память:{get_mem()}\n")
            else:
                #stdscr.addstr(f"Минимальный по числу посещенных городов путь, используя доступные виды транспорта: {result}\n")
                #stdscr.addstr(f"Количество посещенных городов: {len(result) - 1}\n")
                stdscr.addstr(f"{result}\n")
                stdscr.addstr(f"время{time_work/10**9} сек, память:{get_mem()}\n")
            stdscr.addstr("Нажмите любую клавишу для перехода в меню\n")
            stdscr.refresh()
            curses.curs_set(0)
            stdscr.getch()

        elif current_item_index == LIMITCOST_MODE:
            flag_1 = False
            was_start_city_error = False
            while flag_1 == False:
                stdscr.clear()
                if was_start_city_error:
                    stdscr.addstr("Такого города нет, введите другой город отправления\n")
                stdscr.addstr("Введите город отправления:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                start_city = str(stdscr.getstr(), "utf-8", errors="ignore")                        
                if start_city not in city_ind:
                    was_start_city_error = True
                else:
                    flag_1 = True
                    was_start_city_error = False
                            
            #Запуск четвертого алгоритма
            stdscr.clear()
            stdscr.addstr("Введите лимит стоимости:\n")
            stdscr.refresh()
            curses.curs_set(1)
            
            limit_cost = int(str(stdscr.getstr(), "utf-8", errors="ignore"))
            time_work = get_time()
            result = dijkstra_pq(g, start_city, '', prohibited_transport, 'fare', limit_cost)                       
            time_work = get_time() - time_work
            stdscr.clear()
            if result == -1:
                stdscr.addstr(f"Нет городов, достижимых из {start_city} за {limit_cost} рублей, c использованием указанных доступных видов транспорта\n")
                stdscr.addstr(f"время{time_work/10**9} сек, память:{get_mem()}\n")
            else:
                stdscr.addstr(f"Города, достижимые из {start_city} за {limit_cost} рублей:\n")
                for city in result:
                    stdscr.addstr(f'{str(city)}\n')
                #    stdscr.addstr(f"{city}: {result[city]} (стоимость: {result[city]})\n")
                # stdscr.addstr(f"{result}\n")
            stdscr.addstr(f"время{time_work/10**9} сек, память:{get_mem()}\n")
            stdscr.addstr("Нажмите любую клавишу для перехода в меню\n")
            stdscr.refresh()
            curses.curs_set(0)
            stdscr.getch()
                        
        elif current_item_index == LIMITTIME_MODE:
            flag_1 = False
            was_start_city_error = False
            while flag_1 == False:
                stdscr.clear()
                if was_start_city_error:
                    stdscr.addstr("Такого города нет, введите другой город отправления\n")
                stdscr.addstr("Введите город отправления:\n\n")
                stdscr.refresh()
                curses.curs_set(1)

                start_city = str(stdscr.getstr(), "utf-8", errors="ignore")                        
                if start_city not in city_ind:
                    was_start_city_error = True
                else:
                    flag_1 = True
                    was_start_city_error = False

            #Запуск пятого алгоритма		
            stdscr.clear()
            stdscr.addstr("Введите лимит времени:\n")
            stdscr.refresh()
            curses.curs_set(1)
            
            limit_time = int(str(stdscr.getstr(), "utf-8", errors="ignore"))

            time_work = get_time()
            result = dijkstra_pq(g, start_city, '', prohibited_transport, 'time', limit_time)
            time_work = get_time() - time_work
            stdscr.clear()
            if result == -1:
                stdscr.addstr(f"Нет городов, достижимых из {start_city} за {limit_cost} единицу времени, c использованием указанных доступных видов транспорта\n")
                stdscr.addstr(f"время{time_work/10**9} сек, память:{get_mem()}\n")
            else:
                stdscr.addstr(f"Города, достижимые из {start_city} за {limit_time} единицу времени:\n")
                for city in result:
                   stdscr.addstr(f"{str(city)}\n")
                # stdscr.addstr(f"{result}\n")
            stdscr.addstr(f"время{time_work/10**9} сек, память:{get_mem()}\n")
            stdscr.addstr("Нажмите любую клавишу для перехода в меню\n")
            stdscr.refresh()
            curses.curs_set(0)
            stdscr.getch()
                
        elif current_item_index == WANT_TO_EXIT:
            want_to_exit = True                

    curses.endwin()
        
    # r = dijkstra_pq(g, "n0_0_0_0", "n0_9_9_9", set(), 'notttt')
    # print(r)


if __name__ == '__main__':
    curses.wrapper(main)
