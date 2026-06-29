import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import GitHubProvider from "next-auth/providers/github";
import AzureADProvider from "next-auth/providers/azure-ad";
import EmailProvider from "next-auth/providers/email";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.NEXTAUTH_DATABASE_URL,
});

// Manual adapter targeting our prefixed tables. @auth/pg-adapter assumes a
// "users" table with a "name" column; our GOATflow "users" table uses
// "display_name", so we use nextauth_users for the adapter's bookkeeping and
// manage GOATflow users separately via /auth/oauth in the signIn callback.
const emailAdapter = {
  async createVerificationToken(token: { identifier: string; expires: Date; token: string }) {
    const { identifier, expires, token: tok } = token;
    await pool.query(
      "INSERT INTO verification_token (identifier, token, expires) VALUES ($1, $2, $3)",
      [identifier, tok, expires]
    );
    return token;
  },
  async useVerificationToken({ identifier, token }: { identifier: string; token: string }) {
    const result = await pool.query(
      "DELETE FROM verification_token WHERE identifier=$1 AND token=$2 RETURNING identifier, token, expires",
      [identifier, token]
    );
    return result.rows[0] ?? null;
  },
  async getUserByEmail(email: string) {
    const result = await pool.query("SELECT * FROM nextauth_users WHERE email=$1", [email]);
    return result.rows[0] ?? null;
  },
  async createUser(user: { name?: string; email: string; emailVerified?: Date | null; image?: string }) {
    const result = await pool.query(
      "INSERT INTO nextauth_users (name, email, email_verified, image) VALUES ($1, $2, $3, $4) RETURNING *",
      [user.name ?? null, user.email, user.emailVerified ?? null, user.image ?? null]
    );
    return result.rows[0];
  },
  async updateUser(user: { id: string; name?: string; email?: string; emailVerified?: Date | null; image?: string }) {
    const result = await pool.query(
      "UPDATE nextauth_users SET name=$1, email_verified=$2 WHERE id=$3 RETURNING *",
      [user.name ?? null, user.emailVerified ?? null, user.id]
    );
    return result.rows[0];
  },
  async getUser(id: string) {
    const result = await pool.query("SELECT * FROM nextauth_users WHERE id=$1", [id]);
    return result.rows[0] ?? null;
  },
  async getUserByAccount(_: { provider: string; providerAccountId: string }) {
    return null;
  },
  async linkAccount(account: Record<string, unknown>) {
    return account;
  },
  async createSession(session: { sessionToken: string; userId: string; expires: Date }) {
    return session;
  },
  async getSessionAndUser(_sessionToken: string) {
    return null;
  },
  async updateSession(session: { sessionToken: string }) {
    return session;
  },
  async deleteSession(_sessionToken: string) {
    return null;
  },
};

const handler = NextAuth({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  adapter: emailAdapter as any,
  // JWT strategy required even with adapter — adapter handles email verification
  // tokens only; without this, NextAuth uses DB sessions and skips the jwt callback,
  // so goatflow_token set in signIn never reaches the session callback.
  session: { strategy: "jwt" },
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    GitHubProvider({
      clientId: process.env.GITHUB_ID!,
      clientSecret: process.env.GITHUB_SECRET!,
    }),
    AzureADProvider({
      clientId: process.env.AZURE_AD_CLIENT_ID!,
      clientSecret: process.env.AZURE_AD_CLIENT_SECRET!,
      tenantId: process.env.AZURE_AD_TENANT_ID!,
    }),
    EmailProvider({
      server: {
        host: "smtp.resend.com",
        port: 465,
        auth: {
          user: "resend",
          pass: process.env.RESEND_API_KEY!,
        },
      },
      from: "GOATflow <noreply@goatflow.app>",
    }),
  ],
  secret: process.env.NEXTAUTH_SECRET,
  callbacks: {
    async signIn({ user, account }) {
      if (!user.email) return false;
      try {
        // account is null for email magic links in NextAuth v4
        const provider = account?.provider ?? "email";
        const providerId = account?.providerAccountId ?? user.email;
        // API_URL is a server-only var; NEXT_PUBLIC_API_URL is build-time only
        // and may not be available at runtime in Vercel serverless functions
        const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/auth/oauth`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: user.email,
            display_name: user.name ?? user.email.split("@")[0],
            provider,
            provider_id: providerId,
          }),
        });
        console.log("[signIn] oauth response status:", res.status);
        if (!res.ok) {
          console.error("[NextAuth signIn] /auth/oauth responded", res.status, await res.text().catch(() => ""));
          return false;
        }
        const data = await res.json();
        console.log("[signIn] oauth response data keys:", Object.keys(data));
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (user as any).goatflow_token = data.access_token;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (user as any).goatflow_user_id = data.user_id;
        console.log("[signIn] set goatflow_token:", !!data.access_token);
        return true;
      } catch (err) {
        console.error("[NextAuth signIn callback error]", err);
        return false;
      }
    },
    async jwt({ token, user }) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      console.log("[jwt] user present:", !!user, "goatflow_token:", !!(user as any)?.goatflow_token);
      if (user) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        token.goatflow_token = (user as any).goatflow_token;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        token.goatflow_user_id = (user as any).goatflow_user_id;
      }
      console.log("[jwt] token after:", !!token.goatflow_token);
      return token;
    },
    async session({ session, token }) {
      console.log("[session] token.goatflow_token:", !!token.goatflow_token);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (session as any).goatflow_token = token.goatflow_token;
      return session;
    },
  },
  pages: {
    signIn: "/login",
    error: "/login",
  },
});

export { handler as GET, handler as POST };
