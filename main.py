import heapq
import sys

INF = 2**32-1

class Edge:
    def __init__(self, from_city, to_city, transport_type, cruise_time, cruise_fare):
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

    def get_total_time(self):
        return sum([edge.get("time", INF) for edge in self.path])

    def get_total_fare(self):
        return sum([edge.get("fare", INF) for edge in self.path])


class Graph:
    def __init__(self):
        self.graph = {}

    def add_node(self, node: Edge):
        destination = {"time": node.cruise_time, "fare": node.cruise_fare}
        if node.from_city not in self.graph:
            self.graph[node.from_city] = {}
        self.graph[node.from_city][(node.to_city, node.transport_type)] = destination

    def get_node(self, city: str):
        return self.graph.get(city)

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
            if from_city not in city_ind:   
                city_ind[from_city] = id
                ind_city[id] = from_city
                id += 1
            if to_city not in city_ind: 
                city_ind[to_city] = id
                ind_city[id] = to_city
                id += 1
            edges.append(Edge(
                from_city=city_ind[from_city],
                to_city=city_ind[to_city],
                transport_type=trans_ind[transport_type],
                cruise_time=cruise_time,
                cruise_fare=cruise_fare
            ))
    return edges

def dijkstra_min(graph: Graph, start: str, end: str, allowed_transport: str, kind: str):#limit: INF): # kind time or fare
    # создаем список вершин и устанавливаем для каждой вершины метку "бесконечность"
    # кроме стартовой вершины, у которой метка равна 0
    vertices = {vertex: (float("inf"), None) for vertex in graph.graph}  # The second value in the tuple is for transport type
    vertices[city_ind[start]] = (0, None)
    visited = {}
    # создаем очередь с приоритетом и добавляем в нее стартовую вершину
    pq = [(0, city_ind[start])]

    while len(pq) > 0:
        # извлекаем вершину с минимальной меткой
        (current_distance, current_vertex) = heapq.heappop(pq)

        # проверяем, является ли текущая вершина конечной
        # восстанавливаем путь из стартовой вершины в конечную
        if current_vertex == city_ind[end]:
            path = Path()
            while current_vertex != city_ind[start]:
                path.insert(0, current_vertex)
                current_distance, transport_n = vertices[current_vertex]
                current_node = graph.get_node(current_vertex)
                for (neighbor_name, neighbor_transp), neighbor_info in current_node.items():
                    if current_distance - neighbor_info[kind] == vertices[neighbor_name][0]:
                        current_distance -= neighbor_info[kind]
                        current_vertex = neighbor_name
            path.insert(0, start)
            return path, vertices[end]
        # переходим по минимальному значению пути
        for (neighbor_name, neighbor_transp), neighbor_info in graph.get_node(current_vertex).items():
            if ind_trans[neighbor_transp] not in allowed_transport:
                continue
            distance = current_distance + neighbor_info[kind]
            if distance < vertices[neighbor_name][0]:
                vertices[neighbor_name] = (distance, neighbor_transp)
                visited[neighbor_name] = current_vertex
                heapq.heappush(pq, (distance, neighbor_name))
    

all_transport = []
city_ind = {}
ind_city = {}
trans_ind = {}
ind_trans ={}
edges = parse_file(sys.argv[1])
g = Graph()
for edge in edges:
    g.add_node(edge)
print(g.graph)
# vertices = {vertex: (INF, None) for vertex in g.graph if vertex != {}} 
# print(vertices)
shortest_path = dijkstra_min(g, "n0_0_0_0", "n10_11_14_11", "time")
path_string = "->".join([ind_city[edge[1]] for edge in shortest_path.path])
print(shortest_path.get_total_time())
