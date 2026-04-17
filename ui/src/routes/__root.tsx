import { Outlet, Link, createRootRoute, HeadContent, Scripts, useRouter } from "@tanstack/react-router";


function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <div className="mx-auto mb-6 h-16 w-16 rounded-full border-2 border-accent/40 shadow-[0_0_24px_var(--accent)]" />
        <h1 className="font-display text-7xl font-bold text-accent">404</h1>
        <h2 className="mt-4 font-display text-xl font-semibold uppercase tracking-widest text-text-primary">
          Signal Lost
        </h2>
        <p className="mt-2 font-mono text-sm text-text-muted">
          The requested coordinate does not exist in this sector.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md border border-accent/40 bg-accent/10 px-5 py-2 font-display text-sm font-medium uppercase tracking-wider text-accent transition-colors hover:bg-accent/20"
          >
            Return to base
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  const router = useRouter();
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="font-display text-3xl font-bold text-error">System Anomaly</h1>
        <p className="mt-2 font-mono text-sm text-text-muted">{error.message}</p>
        <button
          onClick={() => {
            router.invalidate();
            reset();
          }}
          className="mt-6 inline-flex items-center justify-center rounded-md border border-accent/40 bg-accent/10 px-5 py-2 font-display text-sm uppercase tracking-wider text-accent transition-colors hover:bg-accent/20"
        >
          Retry
        </button>
      </div>
    </div>
  );
}

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Just A Rather Very Intelligent System — orbital control dashboard." },
      { name: "author", content: "J.A.R.V.I.S." },
      { name: "theme-color", content: "#000810" },
      { property: "og:title", content: "J.A.R.V.I.S. Control Center" },
      { property: "og:description", content: "Just A Rather Very Intelligent System — orbital control dashboard." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "twitter:title", content: "J.A.R.V.I.S. Control Center" },
      { name: "twitter:description", content: "Just A Rather Very Intelligent System — orbital control dashboard." },
    ],
    links: [
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&display=swap",
      },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});



function RootShell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  return <Outlet />;
}
