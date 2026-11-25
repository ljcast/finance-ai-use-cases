"""Genera datos 100% sintéticos para el caso 01.

Empresa ficticia: "Hoteles Demo, S.L." (octubre 2026).
Ninguna cifra, contraparte ni patrón procede de una empresa real.
"""
import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(42)

days = pd.date_range("2026-10-01", "2026-10-31", freq="D")
suppliers = ["Proveedor Lavandería", "Proveedor Alimentación", "Proveedor Mantenimiento",
             "Proveedor Suministros", "Proveedor Marketing"]

forecast, actual = [], []

def add(date, cat, counterparty, fc, act=None, desc=""):
    forecast.append((date, cat, fc))
    if act is None:
        act = fc * rng.uniform(0.92, 1.08)          # ruido normal ±8 %
    if act != 0:
        actual.append((date, counterparty, cat, desc or cat, round(act, 2)))

for d in days:
    # Cobros con tarjeta: todos los días
    add(d, "Cobros tarjeta", "Adquirente tarjetas", 12000)
    # Comisiones bancarias: todos los días
    add(d, "Comisiones bancarias", "Banco", -300)
    # Proveedores: días laborables
    if d.weekday() < 5:
        add(d, "Proveedores", rng.choice(suppliers), -6000)
    # Cobros OTA: jueves
    if d.weekday() == 3:
        add(d, "Cobros OTA", "Plataforma de reservas", 28000)
    if d.day == 1:
        add(d, "Alquileres", "Arrendador", -15000)
    if d.day == 20:
        add(d, "Impuestos", "Hacienda", -9000)
    if d.day == 28:
        add(d, "Nóminas", "Nóminas", -38000)

fc = pd.DataFrame(forecast, columns=["date", "category", "forecast_amount"])
bk = pd.DataFrame(actual, columns=["date", "counterparty", "category", "description", "amount"])

# --- Anomalías inyectadas (el análisis debe encontrarlas) --------------------
# 1) Pago duplicado a proveedor (el 14 estaba previsto UN pago de 18.450 €)
fc.loc[(fc.date == "2026-10-14") & (fc.category == "Proveedores"), "forecast_amount"] = -18450
bk = bk[~((bk.date == "2026-10-14") & (bk.category == "Proveedores"))]
dup = pd.DataFrame([("2026-10-14", "Proveedor Mantenimiento", "Proveedores", "Factura 2026-0871", -18450.00)] * 2,
                   columns=bk.columns)
dup["date"] = pd.to_datetime(dup["date"])
bk = pd.concat([bk, dup])

# 2) Caída de cobros con tarjeta el 9 (fallo de terminal)
m = (bk.date == "2026-10-09") & (bk.category == "Cobros tarjeta")
bk.loc[m, "amount"] = 7200.00

# 3) Cobro OTA previsto el 22 que no llega
bk = bk[~((bk.date == "2026-10-22") & (bk.category == "Cobros OTA"))]

# 4) Salida no prevista el 27 (capex)
bk = pd.concat([bk, pd.DataFrame([(pd.Timestamp("2026-10-27"), "Proveedor Reformas", "Capex no previsto",
                                   "Anticipo obra", -52000.00)], columns=bk.columns)])

bk = bk.sort_values(["date", "category"]).reset_index(drop=True)
fc.to_csv(OUT / "cash_forecast.csv", index=False)
bk.to_csv(OUT / "bank_movements.csv", index=False)
print(f"{len(bk)} movimientos y {len(fc)} líneas de previsión en {OUT}")
