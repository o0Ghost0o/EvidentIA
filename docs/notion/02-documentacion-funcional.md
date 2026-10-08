# 📗 Documentación Funcional — EvidentIA
> **Sistema Copiloto de Entorno y Verificación Trazable**  
> **hackIAthon Panamá 4ta edición — TVN Media / Viamatica**  
> **Modalidad Principal:** TVN Media (Editorial) · **Extensión:** Entorno Económico y Bancario  
> **Demo en Vivo:** [https://dev-evidentia.vertexdc.com](https://dev-evidentia.vertexdc.com)

---

## 1. El Reto Editorial y Nuestra Propuesta de Valor

En la era de la sobrecarga informativa, el desafío de una sala de redacción moderna como **TVN Media** ya no es la falta de noticias, sino la **falta de verificación oportuna y contextualizada**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EL PARADIGMA EDITORIAL DE EVIDENTIA                    │
│                                                                             │
│   ❌ La Inmediatez Ciega                    ✅ EvidentIA                    │
│   • 5 medios repitiendo una agencia        • 1 sola procedencia detectada   │
│   • Cifras sueltas sin año ni unidad       • WB:PAN:2023 con unidad oficial │
│   • Alucinaciones de modelos de chat       • Abstención estructurada        │
│   • Notas redactadas a ciegas              • Hecho vs Inferencia rotulado   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Principios Fundamentales
1. **Repetir no es corroborar:** Si diez portales digitales replican el mismo comunicado o teletipo de agencia, no existen diez confirmaciones independientes; existe **una sola procedencia**. EvidentIA colapsa el ruido y penaliza la saturación para no inflar la urgencia artificialmente.
2. **Prioridad no es certeza:** El ranking de la bandeja de entrada clasifica el grado de atención editorial que merece un tema, pero jamás reemplaza el juicio crítico ni decreta una verdad absoluta.
3. **Inteligencia en apoyo, decisión humana en el control (*Human-in-the-Loop*):** La IA sugiere correlaciones, reúne antecedentes y redacta borradores estructurados, pero el periodista y el editor conservan la potestad total de publicación.

---

## 2. Personas de Usuario y Roles

EvidentIA fue diseñado contemplando las dinámicas operativas reales de una cadena de noticias y análisis de entorno:

| Rol / Persona | Reto Diario | Cómo le ayuda EvidentIA |
| :--- | :--- | :--- |
| **Editor/a Jefe** *(Owner/Admin)* | Filtrar cientos de cables diarios, asignar coberturas críticas y evitar fiascos editoriales por noticias falsas. | Dispone de una **Bandeja Priorizada** ordenada por impacto y novedad, con alertas de anomalías y confirmación de fuentes independientes. |
| **Periodista de Investigación** *(Member)* | Perder horas contrastando cifras oficiales (PIB, desempleo) y armando la cronología de los hechos. | Accede a una **Ficha de Investigación** con citas oficiales inmediatas del Banco Mundial e inspección visual en el **Grafo de Causalidad**. |
| **Productor/a Digital** *(Member)* | Redactar en minutos titulares, resúmenes web y copys para redes sociales sin cometer errores factuales. | Utiliza el **Generador Asistido** que entrega borradores con etiquetas explícitas `[HECHO]`, `[DECLARACIÓN]` e `[INFERENCIA]`. |
| **Analista Económico** *(Extensión Banca)* | Monitorear el entorno macroeconómico y detectar señales tempranas de riesgo de liquidez o crédito. | Consulta el boletín de entorno con cruce directo entre eventos noticiosos y series históricas del Banco Mundial. |

---

## 3. Flujos de Trabajo Editoriales (Paso a Paso)

### Flujo 1: Bandeja de Entrada Priorizada (`/`)
El flujo diario comienza en la pantalla principal:
1. **Visualización de Leads:** El periodista observa los temas organizados en tarjetas con sus índices de prioridad ponderada $P$, categoría temática y sello de tiempo.
2. **Desglose de Factores:** Al posicionar el cursor sobre el score, se aprecian los componentes transparentes: Relevancia ($R$), Impacto ($I$), Urgencia ($U$), Novedad ($N$) y Evidencia Corroborada ($E$).
3. **Filtrado Multidimensional:** Búsqueda instantánea por palabras clave o filtros por categoría (Economía, Sociedad, Clima/Sismos, Política).

### Flujo 2: Creación de un Nuevo Lead (`/leads/new`)
Cuando surge una pista periodística de última hora:
1. **Paso 1 (Contexto Inicial):** El redactor ingresa el título preliminar, selecciona la temática y define el alcance ciudadano.
2. **Paso 2 (Recuperación Automática de Evidencia):** El motor semántico consulta en tiempo real el repositorio de noticias, indicadores del Banco Mundial y eventos geofísicos, sugiriendo las fuentes vinculadas.
3. **Paso 3 (Consolidación de Ficha):** Se genera la ficha con el identificador del caso listo para investigación profunda.

### Flujo 3: Ficha de Evidencia y Árbol de Trazabilidad (`/leads/{id}`)
Al abrir cualquier investigación:
1. **Citas Canónicas Inmutables:** Cada afirmación cuantitativa muestra su enlace con formato `[WB:PAN:INDICADOR:AÑO]` (ej. `WB:PAN:NY.GDP.MKTP.KD.ZG:2023`), indicando el año exacto de corte y la unidad (`% anual`).
2. **Modal de Fuentes:** Al presionar cualquier cita, se despliega el modal interactivo con el texto original extraído, medio emisor y enlace a la fuente primaria.
3. **Detección de Vacíos:** Si una afirmación no cuenta con respaldo en el corpus, se marca visualmente con una advertencia amarilla de advertencia (*Evidencia pendiente*).

### Flujo 4: Generador de Borradores con Clasificación Epistémica
Para redactar la pieza editorial:
1. **Selección de Formato:** El periodista elige el formato de salida: *Nota Web TVN*, *Avance Noticiero Central* o *Boletín Económico*.
2. **Generación con Citas:** El modelo genera el texto aplicando estrictamente la regla de marcado:
   - `[HECHO]`: Aseveraciones comprobadas con identificador de fuente.
   - `[DECLARACIÓN]`: Citas textuales de voceros o autoridades.
   - `[INFERENCIA]`: Conclusiones analíticas sobre tendencias.
3. **Respuesta ante Falta de Datos (Abstención):** Si se consulta sobre datos no existentes (ej. *"¿Cuál es la inflación proyectada de diciembre 2026?"*), el sistema emite una abstención explícita explicando qué información falta y qué diligencia debe hacer el periodista ante el MEF o Banco Mundial.

### Flujo 5: Explorador del Grafo de Conocimiento (`/graph`)
Para entender el panorama global de una coyuntura:
1. **Simulación a 60 FPS:** Visualización física en SVG donde las noticias, indicadores y eventos orbitan y se enlazan mediante aristas de fuerza dirigida.
2. **Navegación Interactiva:** El usuario puede arrastrar nodos, hacer zoom en nodos densos y aislar clústeres temáticos (ej. impacto de sismos en carreteras o inflación en canasta básica).
3. **Conexiones Inesperadas:** Permite al periodista descubrir cómo un hecho gremial aislado se conecta con un indicador histórico de productividad agropecuaria.

### Flujo 6: Carga de Datos y Gestión de Plantillas (`/ingest`)
Para actualizar o enriquecer el corpus con nuevas fuentes:
1. **Descarga de Plantillas Oficiales:** Botón de descarga de plantillas estándar para las 4 familias (`plantilla_noticias.csv`, `plantilla_indicadores.csv`, etc.).
2. **Subida Asistida con Validación:** Carga de archivos por arrastrar y soltar con verificación instantánea de columnas y tipos de datos.
3. **Auditoría de Duplicados en Vivo:** Al completarse la carga, se asigna un `upload_id` único y se muestra una insignia verde (*Sin duplicados*) o ámbar (*N duplicados detectados y agrupados*), con acceso a la tabla histórica.

### Flujo 7: Consola de Evaluación Oficial (`/jurado`)
Diseñada especialmente para auditoría técnica y editorial:
1. **Ejecución en Vivo de T01 a T10:** Un solo clic ejecuta las 10 pruebas oficiales del pliego en menos de 7 segundos.
2. **Visualizador Markdown Estilizado:** Reporte técnico completo con alternancia entre vista renderizada de alta legibilidad y código Markdown crudo para descarga y exportación directa.

---

## 4. Casos Prácticos de Aplicación en TVN Media

### Caso A: Huelga Bananera y Afectación Económica en Bocas del Toro
* **Señal:** Dos medios locales reportan bloqueos de vías en Changuinola por reclamos laborales.
* **Procesamiento EvidentIA:**
  - Colapsa las notas en una sola procedencia al detectar similitud léxica superior al 90%.
  - Recupera automáticamente el indicador del Banco Mundial de Exportaciones Agrícolas y Empleo Rural en Panamá.
  - Conecta el caso en el grafo con los antecedentes de 2023.
* **Resultado para TVN:** En 3 minutos, el periodista emite un reporte que no solo narra el bloqueo del día, sino que lo contextualiza con el impacto en el PIB provincial y el precedente histórico.

### Caso B: Sismo en Tierras Altas de Chiriquí
* **Señal:** Registro sísmico del USGS de magnitud 4.8 en el occidente del país.
* **Procesamiento EvidentIA:**
  - Ingesta el GeoJSON con coordenadas precisas, profundidad y radio de alerta.
  - Cruza con noticias de afectaciones viales en el paso de Boquete y Cerro Punta.
* **Resultado para TVN:** Se genera de inmediato una ficha de alerta para el Noticiero del Mediodía con mapa georreferenciado y antecedentes de réplicas en la zona.

### Caso C: Consulta Fuera de Corpus (Simulación de Fallo / Prueba de Fuego)
* **Acción del Usuario:** Se pregunta a la plataforma: *"¿Cuántos turistas llegaron a Panamá hoy y cuál es el veredicto sobre el nuevo plan turístico?"*
* **Comportamiento de EvidentIA:**
  - El sistema detecta que no existen reportes oficiales en el dataset con fecha de corte de hoy.
  - En lugar de inventar estimaciones, activa la **Abstención Estructurada**.
  - Emite un mensaje claro: *"EvidentIA se abstiene de responder. No existen fuentes oficiales publicadas en el corpus para la fecha actual. Se sugiere consultar las estadísticas mensuales de la Autoridad de Turismo de Panamá (ATP)."*

---

## 5. Métricas de Impacto Operativo para TVN

| Indicador Clave de Rendimiento (KPI) | Proceso Tradicional Manual | Con EvidentIA | Impacto Cuantitativo |
| :--- | :--- | :--- | :--- |
| **Tiempo de Preparación de Ficha** | 45 a 60 minutos | 8 a 12 minutos | **Ahorro del 80% en tiempo** |
| **Tasa de Citas Anacrónicas o Erróneas** | Frecuente (cifras de años anteriores sin fecha) | 0% (citas obligatorias con ID y año) | **Riesgo reputacional mitigado a 0** |
| **Detección de Duplicados de Agencia** | Manual y subjetivo | Automático por Jaccard y hashes | **100% de ruido léxico filtrado** |
| **Disponibilidad ante Caídas de Red** | Bloqueo de herramientas en la nube | Transición automática a modo offline (0 USD) | **Operatividad garantizada en 100%** |
