import Link from "next/link";

const TARGET_ROLES = [
  "AI Engineer",
  "ML Engineer",
  "Data Scientist",
  "Data Analyst",
] as const;

export default function CompanyPage() {
  return (
    <div className="min-h-full bg-zinc-50 px-4 py-12">
      <div className="mx-auto max-w-2xl space-y-8">
        <div>
          <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-800">
            ← Back
          </Link>
          <h1 className="mt-4 text-2xl font-semibold text-zinc-900">
            Company search
          </h1>
          <p className="mt-2 text-zinc-600">
            Find key people and matching job openings. (API wiring coming next.)
          </p>
        </div>

        <form className="space-y-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <div>
            <label
              htmlFor="company"
              className="block text-sm font-medium text-zinc-800"
            >
              Company name
            </label>
            <input
              id="company"
              name="company"
              type="text"
              placeholder="e.g. Stripe, Google, Anthropic"
              className="mt-2 w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 outline-none ring-emerald-600 focus:ring-2"
            />
          </div>

          <fieldset>
            <legend className="text-sm font-medium text-zinc-800">
              Target roles
            </legend>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {TARGET_ROLES.map((role) => (
                <label
                  key={role}
                  className="flex cursor-pointer items-center gap-2 rounded-lg border border-zinc-200 px-3 py-2 text-sm hover:bg-zinc-50"
                >
                  <input type="checkbox" name="roles" value={role} />
                  {role}
                </label>
              ))}
            </div>
          </fieldset>

          <button
            type="button"
            disabled
            className="w-full cursor-not-allowed rounded-xl bg-zinc-300 px-4 py-3 text-sm font-medium text-zinc-600"
            title="Coming in next step"
          >
            Search company (coming soon)
          </button>
        </form>
      </div>
    </div>
  );
}
