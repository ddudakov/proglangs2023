import heapq
import sys

all_transport = [] # все виды транспорта
city_ind = {} # city -> ind
ind_city = {} # ind -> city
trans_ind = {} # transport_type -> ind
ind_trans ={} # ind -> transport_type


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

def dijkstra_pq(graph: Graph, start: str, end: str, allowed_transport: list(int), kind: str, lim = 0):
    """
    в зависимости что от нас требуется, типо kind это fare или time
    ну и лимиткост в зависимости какой, но вычисления одинаковые
    """
    start = city_ind[start]
    end = city_ind[end]
    prohibited_transport = set()

    if kind == 'time':
        opt_dist, visited = calc_dijkstra_time(graph, start, prohibited_transport)
        #если ограничений нет, то один путь
        if lim == 0:
            return restore_route_time(opt_dist, visited, start, end)
        allowed_citys = []
        for vertex in visited:  
            if opt_dist[vertex] <= lim:
                allowed_citys.append(restore_route_time(vertex))
        return allowed_citys
    elif kind == 'fare':
        opt_dist, visited = calc_dijkstra_cost(graph, start, prohibited_transport)
        #если ограничений нет, то один путь
        if lim == 0:
            return restore_route_cost(opt_dist, visited, start, end)
        allowed_citys = []
        for vertex in visited:  
            if opt_dist[vertex] <= lim:
                allowed_citys.append(restore_route_cost(vertex))
        return allowed_citys
        pass
    else:
        opt_dist, visited = calc_dijkstra_task1(graph, start, prohibited_transport)
        return restore_route_task1(opt_dist, visited, start, end )
        pass


edges = parse_file(sys.argv[1])
g = Graph()
for edge in edges:
    g.add_node(edge)
# r = dijkstra_pq(g, "n0_0_0_0", "n0_9_9_9", all_transport, 'notttt')
# print(r)
