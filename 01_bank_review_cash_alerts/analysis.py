"""Revisión diaria de bancos y alertas de desviación frente a la previsión de caja.

Reglas deterministas y explicables. Cada alerta queda para revisión humana.
"""
import pandas as pd
from pathlib import Path

DATA = Path(__file__).parent / "data"
OPENING_BALANCE = 180_000      # saldo inicial ficticio
MIN_CASH = 100_000             # umbral de caja mínima (política ficticia)
ABS_THRESHOLD = 3_000          # desviación mínima en € para alertar
PCT_THRESHOLD = 0.20           # desviación mínima en % de la previsión
UNPLANNED_THRESHOLD = 5_000    # movimiento sin previsión que obliga a revisar


def load():
    bk = pd.read_csv(DATA / "bank_movements.csv", parse_dates=["date"])
    fc = pd.read_csv(DATA / "cash_forecast.csv", parse_dates=["date"])
    return bk, fc


def deviations(bk, fc):
    act = bk.groupby(["date", "category"], as_index=False)["amount"].sum()
    df = fc.merge(act, on=["date", "category"], how="outer").fillna({"forecast_amount": 0, "amount": 0})
    df["variance"] = df["amount"] - df["forecast_amount"]
    rows = []
    for r in df.itertuples():
        if r.forecast_amount == 0 and abs(r.amount) >= UNPLANNED_THRESHOLD:
            rows.append((r.date, "Movimiento sin previsión", "Alta",
                         f"{r.category}: {r.amount:,.0f} € sin importe previsto",
                         "Confirmar autorización y actualizar la previsión"))
        elif r.forecast_amount != 0 and r.amount == 0 and r.forecast_amount > 0:
            rows.append((r.date, "Cobro previsto no recibido", "Alta",
                         f"{r.category}: previsto {r.forecast_amount:,.0f} €, recibido 0 €",
                         "Reclamar al cliente o plataforma; revisar fecha de valor"))
        elif r.forecast_amount != 0 and abs(r.variance) >= ABS_THRESHOLD \
                and abs(r.variance) >= PCT_THRESHOLD * abs(r.forecast_amount):
            rows.append((r.date, "Desviación vs previsión", "Media",
                         f"{r.category}: previsto {r.forecast_amount:,.0f} €, real {r.amount:,.0f} € "
                         f"({r.variance:+,.0f} €)",
                         "Pedir explicación al responsable del área"))
    return df, rows


def duplicates(bk):
    rows = []
    out = bk[bk.amount < 0].sort_values("date")
    for (cp, amt), g in out.groupby(["counterparty", "amount"]):
        g = g.reset_index(drop=True)
        for i in range(1, len(g)):
            if (g.loc[i, "date"] - g.loc[i - 1, "date"]).days <= 3:
                rows.append((g.loc[i, "date"], "Posible pago duplicado", "Alta",
                             f"{cp}: dos pagos de {abs(amt):,.2f} € en ≤3 días ({g.loc[i, 'description']})",
                             "Bloquear/recuperar el segundo pago antes del cierre"))
    return rows


def balances(bk, fc):
    d = pd.DataFrame({"date": sorted(set(bk.date) | set(fc.date))})
    d["actual"] = OPENING_BALANCE + d.date.map(bk.groupby("date").amount.sum()).fillna(0).cumsum()
    d["forecast"] = OPENING_BALANCE + d.date.map(fc.groupby("date").forecast_amount.sum()).fillna(0).cumsum()
    rows = [(r.date, "Caja bajo mínimo", "Alta", f"Saldo {r.actual:,.0f} € < mínimo {MIN_CASH:,.0f} €",
             "Activar plan de financiación de tesorería")
            for r in d.itertuples() if r.actual < MIN_CASH]
    return d, rows


def run():
    bk, fc = load()
    _, r1 = deviations(bk, fc)
    r2 = duplicates(bk)
    bal, r3 = balances(bk, fc)
    ex = pd.DataFrame(r1 + r2 + r3, columns=["date", "type", "severity", "detail", "suggested_action"])
    ex = ex.sort_values(["date", "severity"]).reset_index(drop=True)
    ex["reviewer"] = ""
    ex["status"] = "Pendiente"
    return bk, fc, bal, ex


def summary(ex, bal):
    lines = [f"Revisión de caja octubre 2026: {len(ex)} alertas para revisión humana.",
             f"Saldo final real {bal.actual.iloc[-1]:,.0f} € frente a {bal.forecast.iloc[-1]:,.0f} € previsto "
             f"(diferencia {bal.actual.iloc[-1] - bal.forecast.iloc[-1]:+,.0f} €)."]
    for r in ex.itertuples():
        lines.append(f"- {r.date:%d/%m} [{r.severity}] {r.type}: {r.detail} → {r.suggested_action}")
    return "\n".join(lines)


def chart(bal, ex, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(bal.date, bal.forecast, "--", color="#888", label="Previsión")
    ax.plot(bal.date, bal.actual, color="#1f4e79", label="Real")
    ax.axhline(MIN_CASH, color="#c0392b", lw=1, ls=":", label="Caja mínima")
    for d in ex.date.unique():
        v = bal.loc[bal.date == d, "actual"].iloc[0]
        ax.plot(d, v, "o", color="#c0392b", ms=6)
    ax.set_title("Saldo diario real vs previsión (datos sintéticos)")
    ax.set_ylabel("€")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=150)


if __name__ == "__main__":
    bk, fc, bal, ex = run()
    ex.to_csv(Path(__file__).parent / "exceptions.csv", index=False)
    txt = summary(ex, bal)
    (Path(__file__).parent / "daily_summary.md").write_text(txt, encoding="utf-8")
    chart(bal, ex, Path(__file__).parent / "balance_chart.png")
    print(txt)
