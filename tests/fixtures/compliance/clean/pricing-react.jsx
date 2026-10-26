// Requires Amaca tokens.css + card.css + badge.css + button.css loaded globally.
const PLANS = [
  {
    code: "PLN-01",
    name: "Starter",
    price: "€0",
    note: "For trying things out",
    features: ["1 project", "Community support", "Basic analytics"],
    cta: "Start free",
  },
  {
    code: "PLN-02",
    name: "Team",
    price: "€29",
    note: "For teams that ship together",
    features: ["Unlimited projects", "Priority support", "Advanced analytics", "Shared design tokens"],
    cta: "Start 14-day trial",
    recommended: true,
  },
  {
    code: "PLN-03",
    name: "Enterprise",
    price: "Custom",
    note: "For organisations at scale",
    features: ["SSO and audit log", "Dedicated manager", "Custom SLA"],
    cta: "Contact sales",
  },
];

export default function PricingCards() {
  return (
    <section
      aria-labelledby="pricing-title"
      className="mx-auto grid w-full max-w-[var(--content-max)] gap-[var(--s-8)] px-[var(--gutter)] py-[var(--s-16)]"
    >
      <header className="grid gap-[var(--s-3)] text-center">
        <h2
          id="pricing-title"
          className="m-0 text-[length:var(--t-h3-fluid)] font-semibold leading-[var(--lh-snug)] tracking-[var(--tr-tight)]"
        >
          Pricing
        </h2>
        <p className="m-0 text-[length:var(--t-lead)] text-[var(--obsidian-300)]">
          Pick a plan. Change it whenever you need.
        </p>
      </header>

      <div className="grid items-stretch gap-[var(--s-6)] md:grid-cols-3">
        {PLANS.map((plan) => (
          <article
            key={plan.code}
            className="card flex flex-col"
            style={{
              width: "100%",
              ...(plan.recommended
                ? { borderColor: "var(--primary-500)", boxShadow: "var(--sh-glow-soft)" }
                : null),
            }}
          >
            <div className="card-meta">
              <span>{plan.code}</span>
              {plan.recommended && <span className="badge badge-solid">Recommended</span>}
            </div>

            <h3 className="m-0 text-[length:var(--t-h5)] font-semibold leading-[var(--lh-snug)] tracking-[var(--tr-snug)]">
              {plan.name}
            </h3>
            <p className="mb-0 mt-[var(--s-1)] text-[length:var(--t-small)] text-[var(--obsidian-300)]">
              {plan.note}
            </p>

            <p className="mb-0 mt-[var(--s-6)] flex items-baseline gap-[var(--s-2)]">
              <span className="text-[length:var(--t-h3)] font-bold leading-[var(--lh-tight)] tracking-[var(--tr-tight)]">
                {plan.price}
              </span>
              {plan.price !== "Custom" && (
                <span className="text-[length:var(--t-small)] text-[var(--obsidian-300)]">/ month</span>
              )}
            </p>

            <hr
              className="my-[var(--s-6)] border-0"
              style={{ height: "var(--bw-1)", background: "var(--border)" }}
            />

            <ul className="m-0 grid list-none gap-[var(--s-3)] p-0 text-[length:var(--t-body)] text-[var(--obsidian-100)]">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-[var(--s-3)]">
                  <svg
                    aria-hidden="true"
                    viewBox="0 0 20 20"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="mt-[var(--s-0-5)] flex-none text-[var(--primary-400)]"
                    style={{ width: "var(--icon-md)", height: "var(--icon-md)" }}
                  >
                    <path d="M4 10.5l4 4 8-9" />
                  </svg>
                  <span>{f}</span>
                </li>
              ))}
            </ul>

            <div className="card-actions mt-auto pt-[var(--s-6)]">
              <button
                type="button"
                className={`btn ${plan.recommended ? "btn-primary" : "btn-secondary"} w-full`}
              >
                {plan.cta}
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
