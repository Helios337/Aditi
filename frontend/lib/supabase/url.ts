/** Browser uses localhost; server/middleware in Docker uses host.docker.internal. */
export function getSupabaseUrl() {
  return process.env.SUPABASE_URL_INTERNAL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
}
