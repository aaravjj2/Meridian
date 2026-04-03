export type ScreenerContract = {
  market_id: string
  platform: 'kalshi' | 'polymarket'
  category: string
  title: string
  resolution_date: string
  market_prob: number
  model_prob: number
  dislocation: number
  direction: 'market_overpriced' | 'market_underpriced'
  explanation: string
  confidence: number
  scored_at: string
}

// Helper type for creating mock contracts in tests
export type MockScreenerContract = Omit<ScreenerContract, 'dislocation' | 'direction' | 'explanation'> & {
  dislocation?: number
  direction?: ScreenerContract['direction']
  explanation?: string
}
