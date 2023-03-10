from multiprocessing import BoundedSemaphore, Lock, Process, Value, Array, current_process
from time import sleep
import random

N = 5
NPROD = 6


def delay(factor=0.3):
    # sleep para realentizar procesos. Por defecto, el valor que tomaría es 0.3
    sleep(random.random() * factor)

def generar_numero(valor, lista_añadir, posicion):
    """
    funcion que me genera un numero aleatorio entre el 2 y el 15
    """
    valor.value += random.randint(2, 15)
    #hacemos que tarde un poco mas en producir el numero
    delay()
    
    lista_añadir[posicion.value] = valor.value #añadimos el valor generado a la lista
    posicion.value += 1 #actualizamos indice


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


def productor(valor, semaforo_general, semaforo_productor, index, lst_comp, fin):
    """
    Función que produce valores aleatorios y los almacena en una variable compartida,
    usando semáforos para la sincronización.
    """
    for _ in range(N):
        
        #esperamos a que este productor pueda producir
        semaforo_productor.acquire()
                
        #avisamos de que el productor actual va a producir
        print(f"Productor {current_process().name} está produciendo")
        
        #generamos el valor nuevo.
        generar_numero(valor, lst_comp, index)
        
        #damos una señal al semaforo_general para avisar de que este productor ya ha producido.
        semaforo_general.acquire() 
        # printeamos el valor producido por este productor
        print(f"Productor {current_process().name} ha almacenado el valor {valor.value}")
    

    print(f"Productor {current_process().name} ha terminado")
    #esto va a hacer que el productor no vuelva a producir numero
    semaforo_productor.acquire()
    #avisamos al semáforo final de que ya hemos terminado con ete productor
    fin.acquire()
    #actualizamos los valores y le introducimos en la lista
    valor.value = -1
    lst_comp[index.value] = -1
    #damos una señal al semáforo general
    semaforo_general.acquire()

def consumidor(almacen_final, semaforo_general, semaphores, comparacion, index, sem_final):
    # es el indice por el que vamos almacenando en el array final
    almacen_index = 0
    
    while True:
        if semaforo_general.get_value() == 0: #tenemos que ver si todos los productores han producido un valor
            
            #si el semaforo sem_final ha llegado a 0 => ya no tenemos mas elementos para seleccionar el minimo y hemos terminado
            if sem_final.get_value() == 0: 
                break
            
            #comparacion[:] devuelve una lista con todos los elementos que hay en comparacion
            minimo = obtener_minimo(comparacion[:]) #cogemos el elemento minimo del array comparacion 
            delay() #elay para simular que tarda un poco en seleccionar el minimo
            
            #lo printeamos
            print("El mínimo de la lista comparacion es:" , minimo) 
            
            #vemos la posicion en la que estaba el índice para saber de qué productor es el elemento minimo
            index.value = comparacion[:].index(minimo)
            
            #añadimos al array el elemento minimo seleccionado
            almacen_final[almacen_index] = minimo 
            
            #actualizamos el índice del array para saber la posicion y la cantidad de elementos ya añadidos al array final
            almacen_index += 1 
            
            #liberamos el semaforo correspondiente al productor del cual hemos seleccionado el elemento minimo
            semaphores[index.value].release() 
            print("Comparación actual:", comparacion[:]) 
            print("Almacen por el momento", almacen_final[:])
            
            semaforo_general.release() #liberamos el semaforo general para no alterar la lista solucion de minimos y poder cogerlos en orden
            
        else: #si hay algún productor que no nos ha producido todavia, esperamos a que lo haga
            delay()
        
def main():
    almacen_final = Array('i', N * NPROD) #lo que vamos a devolver
    semaforo_general = BoundedSemaphore(NPROD) #nos idicará cuando el consumidor tiene que consumir numeros
    lst_comp = Array('i', NPROD) #array del cual el consumidor va a coger el elemento minimo
    index = Value('i', 0) #valor compartido que nos indica el indice de cada consumidor
    valores_iniciales, semaforos = [],[]
    #lista de valores compartidos para que los productores generen numero. Inicialmente está vacía => -2
    #cada productor va a tener un Lock que les dirá quien puede producir y quien no.
    #semáforo acotado que se va reduciendo en 1 unidad cuando un productor termina de producir
    final = BoundedSemaphore(NPROD)
    
    for i in range(NPROD):
        lst_comp[i] = -2
        valores_iniciales.append(Value('i', -2))
        semaforos.append(Lock())
        
    for i in range(N * NPROD):
        almacen_final[i] = -2

    
    lista_procesos = [Process(target=productor,
                              name=f'p_{i}',
                              args=(valores_iniciales[i],
                                  semaforo_general,
                                  semaforos[i],
                                  index,
                                  lst_comp,
                                  final))
                     for i in range(NPROD)]
    
    consumer = Process(target=consumidor, args=(almacen_final,
                                                semaforo_general,
                                                semaforos,
                                                lst_comp,
                                                index,
                                                final))
    
    for p in lista_procesos:
        p.start()
    consumer.start()
    
    for p in lista_procesos:
        p.join()
    consumer.join()
    
    print("Almacén final", almacen_final[:])
    
if __name__ == "__main__":
    main()
