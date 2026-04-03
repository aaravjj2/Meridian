import RegimeDashboard from '@/components/RegimeDashboard/RegimeDashboard'

export default function MethodologyPage() {
  return (
    <main className="methodology-page" data-testid="methodology-page">
      <RegimeDashboard />
      <article className="methodology-article">
        <h1 data-testid="methodology-heading-how">How Meridian Works</h1>

        <section>
          <h2>What Meridian Does</h2>
          <p>
            Meridian runs an agentic GLM-5.1 research loop that gathers macro evidence, interprets prediction market pricing,
            and streams a cited investment brief while exposing every intermediate reasoning step.
          </p>
        </section>

        <section>
          <h2>How GLM-5.1 Is Used</h2>
          <p>
            The agent receives a strict tool schema, performs multi-step tool calls, and emits trace events for tool_call,
            tool_result, reasoning, and brief_delta before a final complete event.
          </p>
        </section>

        <section>
          <h2 data-testid="methodology-heading-data-sources">Data Sources</h2>
          <table>
            <thead>
              <tr>
                <th scope="col">Source</th>
                <th scope="col">Type</th>
                <th scope="col">Description</th>
                <th scope="col">Update</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>FRED</td>
                <td>Macro series</td>
                <td>Rates, inflation, labor, credit, and growth indicators.</td>
                <td>Daily/Monthly</td>
              </tr>
              <tr>
                <td>Kalshi</td>
                <td>Prediction market</td>
                <td>Binary macro contract probabilities and volume context.</td>
                <td>Intraday</td>
              </tr>
              <tr>
                <td>Polymarket</td>
                <td>Prediction market</td>
                <td>Complementary market pricing for cross-venue dislocation checks.</td>
                <td>Intraday</td>
              </tr>
              <tr>
                <td>SEC EDGAR</td>
                <td>Filings</td>
                <td>Company disclosures chunked for long-context reasoning.</td>
                <td>Event-driven</td>
              </tr>
              <tr>
                <td>News</td>
                <td>Narrative context</td>
                <td>Recent policy and macro headlines with sentiment tags.</td>
                <td>Daily</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section>
          <h2>Fair-Value Model</h2>
          <p>
            Meridian converts relevant macro series into normalized signals, calibrates model probability with a simple
            Platt-style layer, and compares it against market-implied odds to rank dislocation magnitude.
          </p>
        </section>

        <section>
          <h2>Limitations</h2>
          <p>
            The model relies on historical relationships and fixture-backed demo data. Prediction markets can move faster
            than macro releases, and unexplained structural breaks can reduce model reliability.
          </p>
        </section>

        <section>
          <h2>Disclaimer</h2>
          <p>Meridian is a research system and does not provide financial, legal, or investment advice.</p>
        </section>
      </article>
    </main>
  )
}
