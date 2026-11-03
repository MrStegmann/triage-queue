# Notas de Diseño

## 1. Selección de Estructura de Datos Interna y Análisis de Compensaciones (Trade-Offs)

### 1.1 Arquitectura Seleccionada: Deque Multicubeta (`dict[TriageLevel, collections.deque]`)

El servicio de dominio principal (`TriageQueue`) organiza a los pacientes en espera en cubetas de prioridad discretas indexadas por su nivel de triage clínico:

```python
self._buckets: dict[TriageLevel, deque[PatientRecord]] = {
    TriageLevel.CRITICAL: deque(),  # Nivel 1 (Mayor prioridad)
    TriageLevel.URGENT: deque(),    # Nivel 2
    TriageLevel.STANDARD: deque(),  # Nivel 3 (Menor prioridad)
}
```

#### Propiedades Arquitectónicas Clave:
1. **Complejidad Temporal $O(1)$ para Operaciones Principales**:
   - **Encolar (`enqueue`)**: Adición amortizada $O(1)$ a la cola de la cubeta de prioridad designada (`_buckets[patient.triage_level].append(...)`).
   - **Desencolar (`dequeue`)**: Recuperación en peor caso $O(1)$. El algoritmo inspecciona como máximo 3 cubetas fijas en orden clínico estricto (`CRITICAL` $\to$ `URGENT` $\to$ `STANDARD`) y extrae de la cabeza de la primera cubeta no vacía (`bucket.popleft()`). Debido a que el número de niveles de prioridad $K = 3$ es constante, la comprobación de cubetas está acotada en $O(K) = O(1)$.
   - **Inspección (`peek`)**: Inspección de la cabeza en tiempo constante $O(1)$ sin eliminar el elemento (`bucket[0]`).
   - **Estadísticas de Carga de Trabajo (`get_statistics`)**: Recuperación directa $O(1)$ mediante `len(bucket)`.
   - **Instantánea / Listado de la Cola (`list_all`)**: Iteración lineal $O(N)$ a través de las tres cubetas sin modificar el estado ni asignar búferes de ordenamiento intermedios.
2. **FIFO Estricto y Determinista dentro de Cada Nivel**:
   - Los pacientes admitidos en el mismo nivel de triage tienen garantizada la atención en su secuencia exacta de llegada. El `collections.deque` de Python está implementado en C como una lista doblemente enlazada de bloques de tamaño fijo (64 elementos por bloque), lo que garantiza un comportamiento FIFO real sin reasignación de elementos ni reubicación de punteros.
3. **Inmunidad Completa a Relojes y Marcas de Tiempo (Timestamps)**:
   - La prioridad y el orden de llegada no dependen de las marcas de tiempo del sistema (`arrived_at`). Como resultado, la cola es completamente inmune a límites de resolución de marcas de tiempo, colisiones de microsegundos, desviación de reloj (clock drift), ajustes de horario de verano o saltos de sincronización NTP.
4. **Alineación con el Dominio Clínico**:
   - Los sistemas de triage (como el Índice de Severidad de Urgencias o el Sistema de Triage de Mánchester) operan sobre categorías de gravedad discretas, no sobre funciones numéricas continuas. La partición por niveles discretos se ajusta a la realidad médica y mantiene la lógica de dominio transparente.

---

### 1.2 Evaluación Frente a Estructuras de Datos Alternativas

| Arquitectura | Encolar | Desencolar | Peek | Estabilidad FIFO | Memoria / Sobrecarga | Desventaja Principal |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Deque Multicubeta** *(Seleccionada)* | **$O(1)$** | **$O(1)$** | **$O(1)$** | **Estricta y Natural** | **Mínima** | Niveles de prioridad discretos finitos ($K=3$) |
| **`collections.deque` Único** | $O(N)$ | $O(1)$ | $O(1)$ | Manual / Frágil | Mínima | Insertar pacientes críticos en el medio requiere rotación/recorrido de elementos en $O(N)$ |
| **Arreglo Dinámico Ordenado (`list`)** | $O(N)$ | $O(N)$ o $O(1)$ | $O(1)$ | Requiere clave secundaria | Media | La inserción requiere desplazar bloques de memoria ($O(N)$ vía `bisect.insort`) |
| **Montículo Binario Mínimo (`heapq`)** | $O(\log N)$ | $O(\log N)$ | $O(1)$ | Requiere desempate | Alta (Tuplas + estructura de montículo) | La inspección/listado requiere copia destructiva y ordenamiento ($O(N \log N)$) |
| **Tres Colas Sueltas Separadas** | $O(1)$ | $O(1)$ | $O(1)$ | Estricta | Mínima | Falta de encapsulación, estado disperso, estadísticas agregadas propensas a errores |

---

### 1.3 Comparación Detallada con Alternativas

#### Alternativa A: Un único `collections.deque`
- **Cómo funcionaría**: Todos los pacientes residen en una sola cola de doble extremo.
- **Por qué fue rechazada**:
  - Un único `deque` sobresale cuando los elementos son estrictamente por orden de llegada (append en la derecha en $O(1)$, pop desde la izquierda en $O(1)$).
  - Sin embargo, cuando llega un paciente `CRITICAL` o `URGENT`, debe adelantarse a los pacientes `STANDARD` anteriores.
  - En un deque único, la inserción en un índice arbitrario requiere rotar elementos (`deque.rotate()`) o recorrer nodos, tomando un tiempo $O(N)$.
  - Ordenar un deque único en cada admisión cuesta $O(N \log N)$, anulando por completo los beneficios de rendimiento de una estructura de cola.

#### Alternativa B: Un Arreglo Dinámico Ordenado (`list` con `bisect`)
- **Cómo funcionaría**: Los pacientes se mantienen en una `list` contigua de Python, ordenada por `(triage_level, arrival_timestamp)`.
- **Por qué fue rechazada**:
  - Las listas de Python son arreglos contiguos de punteros en memoria.
  - Encontrar el índice de inserción con `bisect` es logarítmico ($O(\log N)$), pero insertar un elemento en el medio o al frente requiere desplazar todos los punteros subsiguientes en memoria, lo cual es una operación $O(N)$.
  - De manera similar, eliminar al paciente de mayor prioridad del principio de una lista estándar (`list.pop(0)`) es $O(N)$ debido a la reasignación de memoria.
  - Mantener la lista en orden inverso permite un `pop()` en $O(1)$, pero la inserción sigue siendo un cuello de botella costoso de $O(N)$ durante condiciones de alta demanda departamental.

#### Alternativa C: Montículo Binario Mínimo (`heapq` / `queue.PriorityQueue`)
- **Cómo funcionaría**: Los pacientes se introducen como tuplas `(triage_level, sequence_counter, patient)` en un montículo binario.
- **Por qué fue rechazada**:
  - **Sobrecarga Algorítmica**: Las operaciones de encolar y desencolar requieren operaciones de subida (*sift-up*) y bajada (*sift-down*) en el árbol, tomando cada una un tiempo $O(\log N)$. Aunque es eficiente para escalas de prioridad grandes y continuas, es estrictamente peor que el rendimiento $O(1)$ ofrecido por los deques por cubetas para niveles de prioridad pequeños y discretos ($K=3$).
  - **Cuellos de Botella de Inspección y Reportes**: Inspeccionar la secuencia completa de la cola en orden de servicio sin mutar el montículo requiere crear una copia profunda y extraer repetidamente todos los elementos, o bien ordenar el arreglo subyacente ($O(N \log N)$). Los deques multicubeta proporcionan esta vista en una sola pasada lineal ($O(N)$).
  - **Secuenciación FIFO Frágil**: Los montículos no pueden comparar de forma nativa objetos `PatientRecord` si sus niveles de prioridad coinciden. Requieren generar un contador de secuencia de desempate explícito y monótonamente creciente (`int`) en cada admisión para evitar errores del tipo `TypeError: unorderable types`.

#### Alternativa D: Tres Variables de Cola Sueltas y Separadas
- **Cómo funcionaría**: Declarar variables independientes `self.critical_queue`, `self.urgent_queue`, `self.standard_queue`.
- **Por qué fue rechazada**:
  - Aunque son asintóticamente idénticas a la arquitectura elegida, las variables sueltas rompen la encapsulación y violan el Principio de Responsabilidad Única.
  - Implementar operaciones globales (como calcular estadísticas de carga de trabajo departamental agregadas, verificar la ocupación total o crear instantáneas inmutables de la cola) conduce a código repetitivo y aumenta el riesgo de errores de sincronización entre primitivas de bloqueo separadas.
  - Mapear la enumeración directamente (`_buckets[TriageLevel]`) produce una raíz agregada limpia que se puede extender fácilmente si se introducen nuevas categorías clínicas (por ejemplo, Nivel 0 de Reanimación o vía rápida).

---

## 2. Control de Concurrencia: Encolado y Desencolado Concurrentes

### 2.1 El Desafío de la Concurrencia

En un departamento de urgencias multiestación, las operaciones clínicas ocurren de forma asíncrona:
- **Trabajador A (Médico / Consumidor)** invoca `dequeue()` para llamar al siguiente paciente para su tratamiento.
- **Trabajador B (Enfermero de Admisión / Productor)** invoca `enqueue(...)` para registrar a un paciente recién llegado categorizado como **Nivel 1 (Crítico)**.

Sin sincronización, pueden surgir dos modos de fallo críticos:
1. **Condición de Carrera y Corrupción del Estado Interno**: La lectura y mutación simultáneas de los punteros internos del deque pueden provocar memoria corrupta, referencias rotas en nodos de listas enlazadas o registros de pacientes perdidos.
2. **Procesamiento Doble**: Dos trabajadores consumidores podrían leer al mismo paciente de mayor prioridad simultáneamente antes de que cualquiera lo marque como eliminado, lo que resultaría en despachos médicos duplicados para el mismo paciente.
3. **Despacho con Prioridad Obsoleta**: El trabajador A podría extraer un paciente `URGENT` a pesar de que ya se hubiera admitido un paciente `CRITICAL`, si los pasos de inspección y extracción no se ejecutan como una unidad indivisible.

---

### 2.2 Arquitectura de Sincronización

Para eliminar las condiciones de carrera y hacer cumplir un comportamiento determinista, `TriageQueue` encapsula un bloqueo reentrante interno (`threading.RLock`). Cada mutación de estado y método de inspección de cola está estrictamente gobernado por este bloqueo:

```python
class TriageQueue:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._buckets = { ... }

    def enqueue(self, patient: PatientRecord) -> None:
        with self._lock:
            self._buckets[patient.triage_level].append(patient)
            self._total_admitted += 1

    def dequeue(self) -> Optional[PatientRecord]:
        with self._lock:
            for level in (TriageLevel.CRITICAL, TriageLevel.URGENT, TriageLevel.STANDARD):
                bucket = self._buckets[level]
                if bucket:
                    return bucket.popleft()
            return None
```

### 2.3 Escenarios de Ejecución Cuando Dos Trabajadores se Intercalan

Debido a que ambas operaciones están protegidas por el mismo bloqueo de exclusión mutua, las solicitudes simultáneas se serializan de forma determinista. Solo son posibles dos secuencias de ejecución:

```
Escenario 1: El Trabajador A (Desencolar) adquiere el bloqueo primero
=============================================================================
Tiempo | Trabajador A (Consumidor: Desencolar) | Trabajador B (Productor: Encolar Crítico)
-------+---------------------------------------+----------------------------------------
t0     | Adquiere el bloqueo                   | Bloqueado esperando el bloqueo
t1     | Evalúa cubetas (Aún no hay Críticos)  | Esperando...
t2     | Extrae el siguiente paciente Urgente  | Esperando...
t3     | Libera el bloqueo y despacha paciente | Esperando...
t4     | Paciente entregado al equipo médico   | Adquiere el bloqueo
t5     | (Listo)                               | Añade el paciente Crítico a la cubeta
t6     |                                       | Libera el bloqueo (Listo)
Resultado: El paciente urgente se despacha de forma segura. El paciente crítico recién 
           encolado queda inmediatamente en la cabeza de la cola, garantizando ser 
           atendido por el siguiente trabajador disponible.
```

```
Escenario 2: El Trabajador B (Encolar Crítico) adquiere el bloqueo primero
=============================================================================
Tiempo | Trabajador B (Productor: Encolar Crítico)| Trabajador A (Consumidor: Desencolar)
-------+------------------------------------------+----------------------------------------
t0     | Adquiere el bloqueo                      | Bloqueado esperando el bloqueo
t1     | Añade el paciente Crítico a la cubeta    | Esperando...
t2     | Incrementa el contador de admisiones     | Esperando...
t3     | Libera el bloqueo (Listo)                | Esperando...
t4     | Admisión registrada                      | Adquiere el bloqueo
t5     |                                          | Evalúa cubetas (encuentra Crítico)
t6     |                                          | Extrae el paciente Crítico (popleft)
t7     |                                          | Libera el bloqueo y despacha paciente
Resultado: El paciente crítico recién llegado se prioriza de inmediato y se despacha 
           al Trabajador A. Cero retraso, cero procesamiento doble.
```

---

## 3. Orden de Mutación de Estado para Prevenir el Procesamiento Doble

### 3.1 El Invariante de "Desvincular Antes de Despachar"

El procesamiento doble ocurre cuando múltiples procesos de trabajadores observan una entidad en un estado activo/en espera y comienzan a trabajar en ella simultáneamente. Para garantizar matemáticamente que el procesamiento doble no pueda ocurrir, las mutaciones de estado deben obedecer la regla de **Desvinculación Atómica Antes del Despacho** (*Atomic Detach-Before-Dispatch*):

```
+-----------------------------------------------------------------------+
|                       SECCIÓN CRÍTICA ATÓMICA                         |
|                                                                       |
|  1. Adquirir Bloqueo (threading.RLock)                                |
|  2. Inspeccionar Cubetas en Orden de Prioridad (Crítico -> Urgente -> Estandar)|
|  3. Extracción Atómica (bucket.popleft())                             |
|     * La referencia del paciente se elimina inmediatamente de la cubeta.|
|     * Los hilos subsiguientes que llamen a dequeue/peek NO pueden      |
|       ver este registro.                                              |
|  4. Actualizar Contadores Agregados y Métricas Internas de Sesión     |
|  5. Liberar Bloqueo                                                   |
+-----------------------------------------------------------------------+
                                   |
                                   v
              6. Despacho / Entrega del Paciente al Trabajador Clínico
```

### 3.2 Orden de Mutación de Estado Paso a Paso

1. **Adquisición del Mutex Exclusivo (`with self._lock:`)**:
   - Bloquea a todos los escritores concurrentes (`enqueue`), lectores (`peek`, `list_all`, `get_statistics`) y otros consumidores (`dequeue`).
2. **Identificación del Paciente Disponible de Mayor Prioridad**:
   - Recorre los niveles de prioridad en orden clínico estricto: `CRITICAL` (1), `URGENT` (2), `STANDARD` (3).
3. **Eliminación Atómica (`bucket.popleft()`)**:
   - El paciente es extraído directamente del deque mientras **todavía se sostiene el bloqueo**.
   - **Invariante Crucial**: La instancia del paciente se separa de la colección *antes* de devolver la referencia al invocador o de ejecutar cualquier lógica externa.
4. **Sincronización de Contadores Agregados**:
   - Cualquier recuento derivado o total acumulado se ajusta dentro del mismo marco bloqueado.
5. **Liberación del Bloqueo**:
   - Termina la sección crítica. Si otro hilo de trabajador estaba esperando por el bloqueo, entra ahora y observa el estado actualizado de la cola. El paciente extraído ya no está presente.
6. **Despacho / Consumo**:
   - El `PatientRecord` devuelto se entrega al invocador para su admisión clínica. Como el registro se eliminó en el paso 3 bajo un bloqueo exclusivo, ningún trabajador concurrente podrá recibir jamás el mismo registro de paciente.

### 3.3 Análisis de Fallos de Órdenes de Mutación Incorrectos

Para resaltar por qué este orden es esencial, considere el antipatrón peligroso de **Despachar Antes de Eliminar**:

> [!CAUTION]
> **Antipatrón (Inspeccionar $\to$ Despachar $\to$ Eliminar)**:
> 1. El Trabajador 1 lee al siguiente paciente mediante `peek()` sin eliminarlo.
> 2. El Trabajador 1 comienza a preparar una habitación o a llamar al paciente.
> 3. El Trabajador 2 llama a `dequeue()`, inspecciona la cola, ve exactamente al mismo paciente y lo despacha a una segunda sala clínica.
> 4. El Trabajador 1 finalmente elimina al paciente de la cola.
> 
> **Consecuencia**: Dos equipos médicos preparan tratamiento para el mismo paciente simultáneamente, mientras otros pacientes urgentes esperan desatendidos.

Al ejecutar estrictamente `bucket.popleft()` **dentro** del límite del bloqueo atómico antes de entregar el objeto, `TriageQueue` hace que el procesamiento doble sea imposible.