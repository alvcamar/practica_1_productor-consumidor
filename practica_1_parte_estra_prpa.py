"""
ALVARO CAMARA FERNANDEZ. PROGRAMACION PARALELA.
"""

from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Lock, Semaphore
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
from random import random, randint

N = 4
NPROD = 6


def delay(factor=1):
    """
    
    Función para introducir un retraso aleatorio en la ejecución del programa.
    
    """
    sleep(random() * factor)


def obtener_minimo(lista):
    """
    
    Devuelve el elemento minimo de la lista de todos los valores que sean positivos
    
    """
    lst = []
    for elem in lista:
        if elem>=0:
            lst.append(elem)
    if lst:
        return min(lst)
    return 


def producir(valor, almacen_productor, sem_empty, sem_non_empty):
    """
    
    Cada productor produce una serie de valores aleatorios en orden creciente que los va almacenando en un almacen (array)
    
    """

    for i in range(N):
        sem_empty.acquire() #bloqueamos el semaforo.

        # Producción del siguiente valor
        print(f"El productor {current_process().name} está produciendo", flush = True)
        #el productor genera un elemento y lo almacena en su almacen
        valor.value += randint(3, 10)
        delay()
        almacen_productor[i] = valor.value
        print(f"El productor {current_process().name} ha almacenado un valor en su correspondiente almacén.", flush = True)

        sem_non_empty.release() #se libera el semaforo on_empty para avisar de que hay elementos disponibles
        delay()

    # El productor ya ha terminado de producir.
    print(f"El productor {current_process().name} ha terminado.", flush = True)

        
def consumidor(almacen_final, almacenes_productores, semaforos_empty, semaforos_non_empty, posiciones, final):
    """
    
    Hace la funcion de consumidor en un problema de productor-consumidor.
    En este caso, coge los almacenes de los productores, coge el elemento minimo 
    y lo introduce en el almacen ordenado del final haciendo uso de semáforos.
    
    """
    # Inicializamos el índice del almacén donde se colocará el mínimo
    almacen_index = 0
    
    #Comprobamos que podemos empezar a coger elementos, sino esperamos.
    for i in range(NPROD):
        semaforos_non_empty[i].acquire()
        semaforos_non_empty[i].release() 

    #Nos metemos en el buble para consumir numeros:
    while True:

        # Comprobamos si se han extraido todos los números
        if final.get_value() == 0:
            break

        #Extraemos los elementos de los almacenes de los productores
        lst_a_comparar = [almacen_i[i] if i < len(almacen_i) else -1 for almacen_i, i in zip(almacenes_productores, posiciones)]
        
        print("Comparación actual:", lst_a_comparar[:])
        
        # cogemos el minimo y metemos un delay para simular que tarda mas de la cuenta.
        minimo = obtener_minimo(lst_a_comparar)
        delay()
        
        #lo añadimos al almacen y actualizamos el indice
        almacen_final[almacen_index] = minimo
        almacen_index += 1
        
        #tenemos que actualizar ahora la informacion sobre el productor del que hemos sacado el minimo:
        
        #indice del minimo para saber a qué productor pertenece
        index_minimo = lst_a_comparar.index(minimo)

        # liberamos el semaforo que le corresponde a dicho productor
        semaforos_empty[index_minimo].release()
        
        # añadimos 1 a la posición del productor del cual hemos cogido el minimo
        posiciones[index_minimo] += 1

        # Si un proceso ha llegado a su fin actualmente, lo notificamos al semaforo fin
        if posiciones[index_minimo] == N:
            final.acquire()

        # Entramos en el semáforo Non-Empty correspondiente
        semaforos_non_empty[index_minimo].acquire()  
        
        # printeamos el almacen actual
        print("Almacén actual:", almacen_final[:])
        delay()
        
def main():
    almacen_ordenado = Array('i', N * NPROD) # Almacenamiento de todos los valores
    valores_generados = [] #lista con los valores que van a ir generando los productores
    posiciones = Array('i', NPROD) # Es un array que contiene la última posición del almacen_productores introducido
    fin = BoundedSemaphore(NPROD) #semaforo que nos indica cuando el consumidor termina de trabajar
    almacenes_productores = [] #lista de arrays con los almacenes de cada productor
    lista_sem_vacios = [] #lista de Lock(), uno para cada productor
    lista_sem_no_vacios = [] #lista de semaforos(0), uno para cada productor
    posiciones = Array('i', NPROD) # Es un array que contiene la última posición del almacen_productores introducido
    
    for i in range(NPROD):
        valores_generados.append(Value('i', -2))
        posiciones[i] = 0 #no hace falta, pues se inicializa en 0
        almacenes_productores.append(Array('i', N))
        lista_sem_vacios.append(Lock())
        lista_sem_no_vacios.append(Semaphore(0))

    for i in range(N * NPROD):
        almacen_ordenado[i] = -2

    for almacen_propio in almacenes_productores:
        for num in range(N):
            almacen_propio[num] = -2
    
    lista = [Process(target=producir,
                              name=f'p_{i}',
                              args=(valores_generados[i],
                                    almacenes_productores[i],
                                    lista_sem_vacios[i],
                                    lista_sem_no_vacios[i]))
                     for i in range(NPROD)]
    
    consumidorr = Process(target=consumidor, 
                         name = "consumidor",
                         args=(almacen_ordenado,
                                almacenes_productores,
                                lista_sem_vacios,
                                lista_sem_no_vacios,
                                posiciones,
                                fin))
    
    for p in lista + [consumidorr]:
        p.start()
    
    for p in lista + [consumidorr]:
        p.join()
    
    print("Almacén final", almacen_ordenado[:])
    
if __name__ == "__main__":
    main()
