from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock, Manager
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
import random



K = 30 #cantidad de números que genera cada productor
NPROD = 3 #número de productores
N = NPROD*(K+1) #cantidad total de números producidos(contando con los -1)


manager = Manager()
result = manager.list() #lista donde se guardarán los números ordenados





def array_con_pos(arr):
    """
    Función auxiliar que dado un array devuelve si tiene algún elemento
    mayor que cero o no.
    """
    for n in arr:
        if n > 0:
            return True
    return False
    
    
    
    

def or_arr(arr):
    """
    Función que dado un array de boolenaos arr devuelve si tiene algún elemento True.
    """
    result = False
    for i in range(len(arr)):
        if arr[i] == 1:
            result = True
    return result
    
    
   

def num_de_false(arr):
    """
    Función auxiliar que dado un array de 0s y 1s, donde 0 representa False y 1 True,
    devuelve el número de False.
    """
    result = 0
    for i in range(len(arr)):
        if arr[i] == 0:
            result = result + 1
    return result
    
   
   
   
    

def get_index(arr,elem):
    """
    Función auxiliar que dados un array arr y un elemento elem nos devuelve 
    el primer índice cuto elemento es elem.
    """
    n = len(arr)
    for i in range(n):
        if arr[i] == elem:
            return i


def min_positivo(arr):
    """
    Función auxiliar que dado un array nos devuelve el menor elemento positivo.
    Para que funcione correctamente el array debe tener al menos un elemento positivo.
    """
    aux = True
    i = 0
    while aux: #encontramos el primer elemento positivo
         if arr[i] > 0:
            m = arr[i]
            aux = False
         else:
            i = i + 1
    for j in range(i,len(arr)): #comparamos con el resto de elementos
        if (arr[j] < m) and (arr[j] > 0):
            m = arr[j]
    return m   
            



def add_data(index,storage,data,mutex,id_prod,aux,p_act):
    """
    Función que dados un array storage, el actual índice index en el que nos encontramos
    en storage, un dato data, un Lock mutex, el identificador del proceso actual
    id_prod, el array auxiliar aux y el array de procesos activos p_act añade a storage
    el dato producido por el proceso.
    """
    mutex.acquire()
    result = data #resultado
    try:
        n = random.randint(result+1,result+5) #tomamos un número aleatorio mayor al dado
        result = n
        storage[index.value] = result
        aux[index.value] = id_prod #añadimos en aux el id del proceso en la posición donde ha sido insertado el dato
        p_act[id_prod] = 1
        index.value = index.value + 1
    finally:
        mutex.release()



def get_data(storage,mutex,aux,p_act):
    """
    Función que dados un array storage y un Lock mutex, añade el mínimo de storage a la lista de resultados result.
    """
    global result
    mutex.acquire()
    try:
        minimo = min(storage)
        if minimo == -1: #hemos encontrado un proceso que ha terminado
            print (f"Consumer {current_process().name} consumiendo {minimo}")
            index_min = get_index(storage,minimo)
            j = aux[index_min] #id del proceso que ha terminado
            storage[index_min] = 0 #como ya hemos tomado el dato ponemos en esa posición un 0
            p_act[j] = 0 #marcamos el proceso como terminado
        else:
            minimo = min_positivo(storage)
            print (f"Consumer {current_process().name} consumiendo {minimo}")
            index_min = get_index(storage,minimo)       
            j = aux[index_min] #id del proceso que ha producido minimo
            storage[index_min] = 0 #como ya hemos tomado el dato ponemos en esa posición un 0
            result.append(minimo)
          
    finally:
        mutex.release()
    return j,minimo




def producer(index,storage, empty,non_empty,mutex,n,aux,p_act):
    data = 0
    print (f"Producer {current_process().name} produciendo")
    for i in range(K):
        empty.acquire()
        add_data(index,storage,data,mutex,n,aux,p_act)
        data = data+5
        """
        Sumamos 5 porque el número aleatorio va de data+1 hasta data+5 y así
        aseguramos que no haya repetciciones.
        """
        print (f"Producer {current_process().name} ha almacenado {storage[index.value-1]}")
        non_empty.release()
    
    empty.acquire()
    storage[index.value] = -1
    aux[index.value] = n
    index.value = index.value + 1
    print (f"Producer {current_process().name} ha almacenado {-1}")
    non_empty.release()
    

 
"""
He hecho dos implementaciones de consumer. En la primera el cnsumidor sólo consume mientras los productores están activos, es decir, una vez que termina de prodducir el último productor el consumidor termina.
En la segunda una vez que terminan todos los productores, el consumidor sigue consumiendo hasta que storage queda vacío.
"""

"""
Primera implementación de consumer.
"""

def consumer(storage,mutex,sem,aux,p_act):
    global result
    for i in range(NPROD): #nos aseguramos que todos los productores han producido al menos un dato
        sem[i][1].acquire()
        #sem[i][1].release()        
    while or_arr(p_act): #mientras no hayan terminado todos los procesos
        print (f"Consumer {current_process().name} desalmacenando")
        (j,data) = get_data(storage,mutex,aux,p_act)
        sem[j][0].release()
        sem[j][1].acquire()

"""
Segunda implementación de consumer, donde se consumen todos los elementos de storage.
"""
"""
def consumer(storage,mutex,sem,aux,p_act):
    global result
    for i in range(NPROD): #nos aseguramos que todos los productores han producido al menos un dato
        sem[i][1].acquire()
        sem[i][1].release()        
    while (or_arr(p_act)) or (array_con_pos(storage)):
    #Hasta que todos los elementos de storage son 0 o -1 el consumidor no termina.
        print (f"Consumer {current_process().name} desalmacenando")
        (j,data) = get_data(storage,mutex,aux,p_act)
        if data != -1:
            sem[j][0].release()
            sem[j][1].acquire()
"""
         
   
def main():
    global N
    storage = Array('i', N) #array común a todos los procesos donde estos guardan los números producidos
    index = Value('i', 0) #marca el índice donde nos encontramos actualmente en storage
    aux = Array('i',N)
    """
    aux es un array común que guarda en la posición i el id del proceso que ha generado el número de la
    posición i de storage.
    """
    p_act = Array('i',NPROD) #número de procesos que no han terminado
    lp = []
    sem = [] #lista de semáforos de los procesos
    mutex = Lock()
    for i in range(NPROD):
        empty = BoundedSemaphore(K+1)
        non_empty = Semaphore(0)
        sem.append([empty,non_empty])
    c = Process(target=consumer, name='cons',args=(storage,mutex,sem,aux,p_act))
    
    for n in range(NPROD):
        lp.append(Process(target=producer,name=f'prod_{n}',args=(index,storage,sem[n][0],sem[n][1],mutex,n,aux,p_act)))
        
    c.start()
    
    for p in lp:
        p.start()
       
    for p in lp:
        p.join()
    c.join()
    
    print(result)
    print("fin")



    
if __name__ == "__main__":
    main()












