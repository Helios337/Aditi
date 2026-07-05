/**
 * Browser requests use the public URL, while server-side requests in Docker may need
 * an internal hostname. Keep the auth cookie name stable so both clients read the
 * same session even when the hostnames differ.
 */
export const SUPABASE_AUTH_COOKIE_NAME = "sb-aditi-auth-token";

export function getSupabaseUrl() {
  return process.env.SUPABASE_URL_INTERNAL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
}
