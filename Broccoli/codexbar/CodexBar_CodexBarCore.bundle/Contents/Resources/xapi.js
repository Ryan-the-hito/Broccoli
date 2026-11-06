defineProvider({
  id: "xapi",
  name: "X API",
  settings: [],
  endpoints: ["https://console.x.com"],
  capabilities: ["browser-cookies", "http-status"],
  cookieDomains: ["x.com", "console.x.com"],
  cookiePolicy: {
    selection: "request-url",
    cache: "nonpersistent",
    imports: "access-gated",
    requiredCookies: ["auth_token", "ct0"],
    headerEcho: { origin: "https://console.x.com", cookie: "ct0", header: "X-CSRF-Token" },
  },
  async fetchUsage(ctx) {
    const domain = "console.x.com";
    if (ctx.browser.availability(domain) === "off") throw ctx.fail.missingCredential("X API cookies are disabled.");
    const invalid = () => {
      throw ctx.fail.parseFailure("X API returned an unrecognized account or dollar balance.");
    };
    const amount = (value) => (typeof value === "number" && Number.isFinite(value) ? value : invalid());
    const expired = ctx.fail.authenticationExpired("X API session expired. Sign in to console.x.com again.");
    let rejected = false;
    for await (const session of ctx.browser.sessions(domain)) {
      const request = async (path) => {
        const response = await ctx.http.get(`https://console.x.com${path}`, {
          cookieSession: session.id,
          headers: { Accept: "application/json" },
        });
        if (response.status === 401) throw expired;
        if (response.status === 403) throw ctx.fail.permissionDenied("X developer console access was denied.");
        if (response.status === 429)
          throw ctx.fail.rateLimited("X API console is rate limited. Wait before refreshing.");
        if (response.status >= 500) throw ctx.fail.providerUnavailable("X developer console is unavailable.");
        let json;
        try {
          json = JSON.parse(response.bodyText);
        } catch {
          if (response.status === 200) return invalid();
        }
        // The console also reports expired authentication as HTTP 400 / code 215.
        if (response.status === 400 && Array.isArray(json?.errors) && json.errors.some((error) => error?.code === 215))
          throw expired;
        if (response.status !== 200) throw ctx.fail.apiFailure(`X developer console returned HTTP ${response.status}.`);
        return json;
      };
      try {
        const me = await request("/api/me");
        const id = me?.account?.id;
        const account = Number.isSafeInteger(id) && id >= 0 ? String(id) : id;
        if (typeof account !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(account)) return invalid();
        const credits = await request(`/api/accounts/${account}/credits`);
        // The console renders these directly as dollars; its spend endpoint uses different units.
        const paid = amount(credits?.credits?.balance);
        const free = credits?.freeCredits === undefined ? 0 : amount(credits.freeCredits?.balance);
        const balance = amount(paid + free);
        return {
          cost: { used: 0, balance, currency: "USD", period: "Prepaid credits" },
          details: [
            {
              title: "Credits",
              rows: [
                { label: "Balance", value: ctx.format.currency(balance, "USD"), usageValue: balance },
                { label: "Purchased credits", value: ctx.format.currency(paid, "USD") },
                { label: "Free credits", value: ctx.format.currency(free, "USD") },
              ],
            },
          ],
          identity: { loginMethod: "Browser session" },
          dataConfidence: "exact",
        };
      } catch (error) {
        if (error !== expired) throw error;
        ctx.browser.rejectCookie(domain, session);
        rejected = true;
      }
    }
    if (rejected) throw expired;
    throw ctx.fail.missingCredential(
      `Sign in to console.x.com. Supported browsers: ${ctx.browser.supportedBrowsers}. Or paste its Cookie header.`,
    );
  },
});
