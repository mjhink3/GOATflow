import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import GitHubProvider from "next-auth/providers/github";
import AzureADProvider from "next-auth/providers/azure-ad";
import EmailProvider from "next-auth/providers/email";
import { Pool } from "pg";
import PostgresAdapter from "@auth/pg-adapter";

const pool = new Pool({
  connectionString: process.env.NEXTAUTH_DATABASE_URL,
});

const handler = NextAuth({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  adapter: PostgresAdapter(pool) as any,
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
        const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
        const res = await fetch(`${apiUrl}/auth/oauth`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: user.email,
            display_name: user.name ?? user.email.split("@")[0],
            provider: account?.provider ?? "email",
            provider_id: account?.providerAccountId ?? user.email,
          }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        (user as any).goatflow_token = data.access_token;
        (user as any).goatflow_user_id = data.user_id;
        return true;
      } catch {
        return false;
      }
    },
    async jwt({ token, user }) {
      if (user) {
        token.goatflow_token = (user as any).goatflow_token;
        token.goatflow_user_id = (user as any).goatflow_user_id;
      }
      return token;
    },
    async session({ session, token }) {
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
