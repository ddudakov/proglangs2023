import heapq
import sys

INF = 2**32

class Edge:
    def __init__(self, from_city: str, to_city: str, transport_type: str, cruise_time: int, cruise_fare: int):
        self.from_city = from_city
        self.to_city = to_city
        self.transport_type = transport_type
        self.cruise_time = cruise_time
        self.cruise_fare = cruise_fare
    def add_edge(self):
        # Проверяем, есть ли уже данный город в словаре graph
        if self.from_city not in graph:
            graph[self.from_city] = {}
        if to_city not in graph:
            graph[to_city] = {}
        # Добавляем ребро от города отправления к городу прибытия
        graph[self.from_city][self.to_city] = (self.transport_type, self.cruise_time, self.cruise_fare)

class Path:
    def __init__(self):
        self.path = []

    def __getitem__(self, index):
        return self.path[index]

    def __add__(self, edge):
        new_path = Path()
        new_path.path = self.path + [edge]
        return new_path

    def get_total_time(self):
        return sum([edge.cruise_time for edge in self.path])

    def get_total_fare(self):
        return sum([edge.cruise_fare for edge in self.path])

def dijkstra(graph, start, end, allowed_transport, kind):
    # создаем список вершин и устанавливаем для каждой вершины метку "бесконечность"
    # кроме стартовой вершины, у которой метка равна 0
    vertices = {vertex: INF for vertex in graph}
    vertices[start] = 0

    # создаем очередь с приоритетом и добавляем в нее стартовую вершину
    pq = [(0, start)]

    while len(pq) > 0:
        # извлекаем вершину с минимальной меткой
        (current_distance, current_vertex) = heapq.heappop(pq)

        # проверяем, является ли текущая вершина конечной
        if current_vertex == end:
            break

        # проходим по всем соседним вершинам
        for neighbor, transport_type, cruise_time, cruise_fare in graph[current_vertex]:
            # проверяем, соответствует ли тип транспорта допустимым значениям
            if transport_type in allowed_transport:
                # вычисляем длину пути до соседней вершины через текущую вершину
                new_distance = cruise_fare if kind == "cost" else cruise_time
                distance = current_distance + new_distance

                # если длина пути меньше, чем сохраненная ранее в вершине, то обновляем ее метку
                if distance < vertices[neighbor]:
                    vertices[neighbor] = distance
                    heapq.heappush(pq, (distance, neighbor))

    # восстанавливаем путь из стартовой вершины в конечную
    path = []
    current = end
    while current != start:
        path.insert(0, current)
        for neighbor, _, cruise_time, cruise_fare in graph[current]:
            current_weight = cruise_fare if kind == 'cost' else cruise_time
            if neighbor == current and current_distance - current_weight == vertices[neighbor]:
                current_distance -= current_weight
                current = neighbor
                break

    path.insert(0, start)

    return path, vertices[end]

def dijkstra_with_limit(graph, start, end, transport_types, kind, limit):
    distances = {start: (0, Path())}
    heap = [(0, start)]
    visited = set()
    
    while heap:
        (distance, current) = heapq.heappop(heap)
        
        if current in visited:
            continue
        
        visited.add(current)

        for edge_id, edge in graph.items():
            if edge.transport_type not in transport_types:
                continue
                
            if edge.from_city == current:
                new_distance = distances[current][0] + edge.cruise_fare if kind == 'cost' else distances[current][0] + edge.cruise_time
                
                if new_distance <= limit and (edge.to_city not in distances or new_distance < distances[edge.to_city][0]):
                    distances[edge.to_city] = (new_distance, distances[current][1] + edge)
                    heapq.heappush(heap, (new_distance, edge.to_city))
    
    if end not in distances:
        return None
    
    return distances[end][1]

graph = {}
all_transport = []
city_ind = {}
ind_city = {}
with open(sys.argv[1], 'r') as f:
        id = 0
        for line in f:
            # Игнорируем комментарии и пустые строки
            if line.startswith('#') or not line.strip():
                continue
            from_city, to_city, transport_type, cruise_time, cruise_fare = [l.strip('"') for l in line.strip().split()]
            if transport_type not in all_transport:
                all_transport.append(transport_type)
            info = Edge(from_city, to_city, transport_type, cruise_time, cruise_fare)
            info.add_edge()
            if from_city in city_ind: 
                continue
            else:  
                city_ind[from_city] = id
                ind_city[id] = from_city
                id += 1
            if to_city in city_ind: 
                continue
            else:
                city_ind[to_city] = id
                ind_city[id] = to_city
                id += 1 

print("Есть 5 доступных режимов работы программы:\n 1. Среди кратчайших по времени путей между двумя городами найти путь минимальной стоимости.\n 2. Среди минимальных по стоимоcти путей между двумя городами найти кратчайший по времени путь.\n 3. Найти путь между двумя городами, минимальный по числу посещенных городов.\n 4. Найти множество городов, достижимых из города отправления не более чем за ограниченную сумму денег.\n 5. Найти множество городов, достижимых из города отправления не более чем за ограниченное количество времени.\n")

print("Выберите режим работы, введите соответствующую режиму цифру")
mode = input()
if mode=="1":
    print("Введите город отправления: ")
    from_city = input()
    print("Введите город прибытия: ")
    to_city = input()
    print("Вывод всех доступных транспортов: ")
    print(all_transport)

    result = dijkstra(graph, from_city, to_city, all_transport, 'time')
    if result is None:
        print("Целевой город недостижим при заданных параметрах")
    else:
        path, time = result
        print("Путь:", " -> ".join(path))
        print("Время: ", time)
        
elif mode=="2": 
    print("Введите город отправления: ")
    city_from = input()
    print("Введите город прибытия: ")
    city_to = input()
    print("Вывод всех доступных транспортов: ")
    print(all_transport)
    result = dijkstra(graph, city_from, city_to, all_transport, 'cost')
    if result is None:
        print("Целевой город недостижим при заданных параметрах")
    else:
        path, cost = result
        print("Путь:", " -> ".join(path))
        print("Стоимость: ", cost)
#print(graph['n0_0_0_0'].items())
#elif mode=="3":

elif mode=="4":
    print("Введите город отправления: ")
    from_city = input()
    print("Введите ограничение по стоимости: ")
    limit_cost = input()
    print("Вывод всех доступных транспортов: ")
    print(all_transport)
    dijkstra_with_limit(from_city, all_transport, 'cost', limit_cost)

elif mode=="5":
    print("Введите город отправления: ")
    from_city = input()
    print("Введите ограничение по времени: ")
    limit_time = input()
    print("Вывод всех доступных транспортов: ")
    print(all_transport)
    dijkstra_with_limit(from_city, all_transport, 'time', limit_time)
