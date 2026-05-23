export type ServiceConfig = {
  llm: { provider: string; configured: boolean };
  serpapi: { configured: boolean; disabled: boolean; available: boolean };
  hunter: { configured: boolean };
};
