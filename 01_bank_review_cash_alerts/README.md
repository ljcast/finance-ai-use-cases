# Caso 01 · Revisión diaria de bancos y alertas de desviación de caja

> Demostración con **datos 100 % sintéticos** de una empresa ficticia ("Hoteles Demo, S.L."). No es una implantación real.

## Problema de negocio
Tesorería revisa a mano los movimientos bancarios y los compara con la previsión de caja. Es lento, y los errores (pagos duplicados, cobros que no llegan, salidas no previstas) se detectan tarde, a menudo en el cierre.

## Qué hace
1. Compara cada día y categoría el movimiento real con la previsión.
2. Aplica cuatro controles: desviación material, cobro previsto no recibido, movimiento sin previsión y posible pago duplicado. Añade una alerta de caja bajo mínimo.
3. Genera `exceptions.csv` (lista de alertas con acción sugerida, revisor y estado), un resumen diario en texto y un gráfico de saldo.

## Resultado con los datos de ejemplo
Se inyectaron 4 incidencias y el análisis las encuentra todas (5 alertas, porque el duplicado dispara dos reglas):

| Fecha | Alerta | Qué ocurre |
|---|---|---|
| 09/10 | Desviación | Cobros con tarjeta 40 % por debajo de lo previsto |
| 14/10 | Posible pago duplicado | Dos pagos iguales a un proveedor |
| 22/10 | Cobro no recibido | Cobro OTA de 28.000 € que no llega |
| 27/10 | Sin previsión | Salida de 52.000 € no prevista |

## Controles y límites
- **Humano en el circuito:** el programa no mueve dinero ni corrige nada; propone y una persona decide.
- **Umbrales ajustables** (3.000 € y 20 %): hay que calibrarlos con datos reales para evitar falsos positivos.
- **No cubre:** conciliación contable completa, fechas valor, multidivisa ni previsiones intradía.
- **Capa de IA (opcional, no incluida):** un modelo de lenguaje podría redactar el resumen a partir de `exceptions.csv`. Se excluye para que el demo sea reproducible y sin enviar datos a terceros.

## Cómo ejecutarlo
```bash
python generate_data.py   # crea data/*.csv
python analysis.py        # crea exceptions.csv, daily_summary.md, balance_chart.png
```
Requiere `pandas` y `matplotlib`. El cuaderno `notebook.ipynb` recorre los mismos pasos.
