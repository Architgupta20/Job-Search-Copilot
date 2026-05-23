/** Shared form field styles — always dark text on white fields. */

export const fieldLabelClass = "block text-sm font-medium text-zinc-900";

export const fieldLabelSmClass = "block text-xs font-medium text-zinc-900";

export const fieldInputClass =
  "mt-1 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/30";

export const fieldTextareaClass = `${fieldInputClass} resize-y`;

export const fieldSelectClass = fieldInputClass;

export const checkboxClass =
  "h-4 w-4 shrink-0 rounded border-zinc-300 text-emerald-600 focus:ring-2 focus:ring-emerald-600/40";

/** Job role tile — highlights when checkbox is checked. */
export const roleOptionClass =
  "flex cursor-pointer items-center gap-2.5 rounded-lg border border-zinc-200 bg-white px-3 py-2.5 text-sm text-zinc-800 transition hover:border-zinc-300 hover:bg-zinc-50 has-[:checked]:border-emerald-600 has-[:checked]:bg-emerald-50 has-[:checked]:font-semibold has-[:checked]:text-zinc-900";
