"""Entry point della GUI: flusso a step per risolvere una decklist e
calcolare il piano di acquisto piu' economico su CardTrader.
"""

import threading
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, WORD, X, Y

from api.cardtrader import (
    CardTraderAuthError,
    CardTraderClient,
    CardTraderError,
    build_blueprint_index,
)
from api.moxfield import parse_decklist
from core.analyzer import CONDITION_RANK, filter_listings
from core.optimizer import optimize
from core.resolver import resolve

BLUEPRINT_INDEX_PATH = "blueprints_index.json"
CONDITIONS = sorted(CONDITION_RANK, key=CONDITION_RANK.get)


class App(ttk.Window):
    """Finestra principale: decklist -> risoluzione -> preferenze -> piano."""

    def __init__(self) -> None:
        super().__init__(themename="darkly", title="CardTrader Deck Optimizer")
        self.geometry("820x680")
        self.minsize(700, 600)

        self.client: CardTraderClient | None = None
        self.blueprint_index: dict | None = None
        # {nome_carta: BlueprintInfo} per le carte risolte con successo.
        self.resolved_cards: dict[str, object] = {}

        self._build_step1()
        self._build_step2()
        self._build_step3()
        self._build_step4()

        self.after(100, self._init_client)

    # ------------------------------------------------------------------
    # Setup client
    # ------------------------------------------------------------------

    def _init_client(self) -> None:
        def task() -> None:
            try:
                client = CardTraderClient()
                client.get_info()
            except CardTraderError as exc:
                self.after(0, lambda: self._on_client_error(exc))
                return
            self.client = client

        threading.Thread(target=task, daemon=True).start()

    def _on_client_error(self, exc: CardTraderError) -> None:
        messagebox.showerror("Errore CardTrader", str(exc))
        self.resolve_button.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Step 1: decklist
    # ------------------------------------------------------------------

    def _build_step1(self) -> None:
        frame = ttk.Labelframe(self, text="1. Decklist", padding=10)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=(10, 5))

        self.decklist_text = ttk.ScrolledText(frame, height=10, wrap=WORD)
        self.decklist_text.pack(fill=BOTH, expand=True)

        self.resolve_button = ttk.Button(
            frame, text="Risolvi", command=self._on_resolve, bootstyle="primary"
        )
        self.resolve_button.pack(anchor="e", pady=(8, 0))

    # ------------------------------------------------------------------
    # Step 2: risoluzione carte
    # ------------------------------------------------------------------

    def _build_step2(self) -> None:
        frame = ttk.Labelframe(self, text="2. Carte non trovate", padding=10)
        frame.pack(fill=X, padx=10, pady=5)

        self.unresolved_list = tk.Listbox(frame, height=5)
        self.unresolved_list.pack(fill=X)

        self.step2_status = ttk.Label(frame, text="")
        self.step2_status.pack(anchor="w", pady=(5, 0))

    def _on_resolve(self) -> None:
        if self.client is None:
            messagebox.showerror(
                "Errore CardTrader",
                "Token API non impostato o non valido: impossibile continuare.",
            )
            return

        entries = parse_decklist(self.decklist_text.get("1.0", tk.END))
        if not entries:
            messagebox.showwarning(
                "Decklist vuota", "Incolla una decklist valida prima di continuare."
            )
            return

        self.resolve_button.configure(state=tk.DISABLED)
        self.unresolved_list.delete(0, tk.END)
        self.step2_status.configure(text="Risoluzione in corso...")

        def task() -> None:
            try:
                blueprint_index = self._load_blueprint_index()
            except CardTraderError as exc:
                self.after(0, lambda: self._on_resolve_error(exc))
                return

            resolved: dict[str, object] = {}
            unresolved: list[str] = []
            for name, _quantity in entries:
                info = resolve(name, blueprint_index)
                if info is None:
                    unresolved.append(name)
                else:
                    resolved[name] = info

            self.after(0, lambda: self._on_resolve_done(resolved, unresolved))

        threading.Thread(target=task, daemon=True).start()

    def _load_blueprint_index(self) -> dict:
        if self.blueprint_index is None:
            self.blueprint_index = build_blueprint_index(
                self.client, BLUEPRINT_INDEX_PATH
            )
        return self.blueprint_index

    def _on_resolve_error(self, exc: CardTraderError) -> None:
        self.resolve_button.configure(state=tk.NORMAL)
        self.step2_status.configure(text="")
        messagebox.showerror("Errore CardTrader", str(exc))

    def _on_resolve_done(
        self, resolved: dict[str, object], unresolved: list[str]
    ) -> None:
        self.resolve_button.configure(state=tk.NORMAL)
        self.resolved_cards = resolved

        for name in unresolved:
            self.unresolved_list.insert(tk.END, name)

        if unresolved:
            self.step2_status.configure(
                text=f"{len(unresolved)} carta/e non trovata/e su {len(resolved) + len(unresolved)}."
            )
        else:
            self.step2_status.configure(text="Tutte le carte sono state trovate.")

        if resolved:
            self.analyze_button.configure(state=tk.NORMAL)
        else:
            self.analyze_button.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Step 3: preferenze
    # ------------------------------------------------------------------

    def _build_step3(self) -> None:
        frame = ttk.Labelframe(self, text="3. Preferenze", padding=10)
        frame.pack(fill=X, padx=10, pady=5)

        ttk.Label(frame, text="Lingua:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.language_var = tk.StringVar(value="en")
        ttk.Combobox(
            frame,
            textvariable=self.language_var,
            values=["en", "it", "de", "fr", "es", "ja"],
            width=8,
        ).grid(row=0, column=1, sticky="w", padx=(0, 20))

        ttk.Label(frame, text="Condizione minima:").grid(
            row=0, column=2, sticky="w", padx=(0, 5)
        )
        self.condition_var = tk.StringVar(value="Near Mint")
        ttk.Combobox(
            frame,
            textvariable=self.condition_var,
            values=CONDITIONS,
            state="readonly",
            width=16,
        ).grid(row=0, column=3, sticky="w", padx=(0, 20))

        self.foil_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Foil", variable=self.foil_var).grid(
            row=0, column=4, sticky="w"
        )

    # ------------------------------------------------------------------
    # Step 4: analisi e piano
    # ------------------------------------------------------------------

    def _build_step4(self) -> None:
        frame = ttk.Labelframe(self, text="4. Piano d'acquisto", padding=10)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=(5, 10))

        self.analyze_button = ttk.Button(
            frame,
            text="Analizza",
            command=self._on_analyze,
            bootstyle="success",
            state=tk.DISABLED,
        )
        self.analyze_button.pack(anchor="e")

        self.step4_status = ttk.Label(frame, text="")
        self.step4_status.pack(anchor="w", pady=(5, 0))

        columns = ("seller", "card", "price")
        self.plan_tree = ttk.Treeview(
            frame, columns=columns, show="headings", height=12
        )
        self.plan_tree.heading("seller", text="Venditore")
        self.plan_tree.heading("card", text="Carta")
        self.plan_tree.heading("price", text="Prezzo")
        self.plan_tree.column("seller", width=180)
        self.plan_tree.column("card", width=320)
        self.plan_tree.column("price", width=100, anchor="e")
        self.plan_tree.pack(fill=BOTH, expand=True, pady=(8, 0))

        self.total_label = ttk.Label(frame, text="", font=("TkDefaultFont", 10, "bold"))
        self.total_label.pack(anchor="e", pady=(8, 0))

    def _on_analyze(self) -> None:
        if not self.resolved_cards:
            messagebox.showwarning(
                "Nessuna carta risolta", "Risolvi la decklist prima di analizzare."
            )
            return

        language = self.language_var.get().strip()
        min_condition = self.condition_var.get()
        foil = self.foil_var.get()

        self.analyze_button.configure(state=tk.DISABLED)
        self.step4_status.configure(text="Analisi in corso...")
        for row in self.plan_tree.get_children():
            self.plan_tree.delete(row)
        self.total_label.configure(text="")

        def task() -> None:
            card_listings: dict[str, list[dict]] = {}
            missing: list[str] = []
            try:
                for name, info in self.resolved_cards.items():
                    listings: list[dict] = []
                    for blueprint in info.blueprints:
                        listings.extend(
                            self.client.get_marketplace_products(blueprint["id"])
                        )
                    filtered, _best = filter_listings(
                        listings, language, min_condition, foil
                    )
                    if filtered:
                        card_listings[name] = filtered
                    else:
                        missing.append(name)
            except CardTraderError as exc:
                self.after(0, lambda: self._on_analyze_error(exc))
                return

            plan = optimize(card_listings) if card_listings else {
                "sellers": {},
                "total_cents": 0,
            }
            self.after(0, lambda: self._on_analyze_done(plan, missing))

        threading.Thread(target=task, daemon=True).start()

    def _on_analyze_error(self, exc: CardTraderError) -> None:
        self.analyze_button.configure(state=tk.NORMAL)
        self.step4_status.configure(text="")
        messagebox.showerror("Errore CardTrader", str(exc))

    def _on_analyze_done(self, plan: dict, missing: list[str]) -> None:
        self.analyze_button.configure(state=tk.NORMAL)

        for seller_id, purchases in plan["sellers"].items():
            for card_name, listing in purchases:
                seller_name = listing["user"].get("username", str(seller_id))
                price = listing["price"]["cents"] / 100
                self.plan_tree.insert(
                    "", tk.END, values=(seller_name, card_name, f"{price:.2f}")
                )

        total = plan["total_cents"] / 100
        self.total_label.configure(
            text=f"Totale: {total:.2f} — {len(plan['sellers'])} venditore/i"
        )

        if missing:
            self.step4_status.configure(
                text=f"{len(missing)} carta/e senza listing disponibili con questi filtri: "
                + ", ".join(missing)
            )
        else:
            self.step4_status.configure(text="")


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
