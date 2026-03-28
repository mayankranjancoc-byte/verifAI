import VerdictBlock from './VerdictBlock'
import ClaimHeatmap from './ClaimHeatmap'
import HeatmapBlock from './HeatmapBlock'
import ContextDrift from './ContextDrift'
import KeyInsights from './KeyInsights'
import TrustTrail from './TrustTrail'
import EmotionExploitPanel from './EmotionExploitPanel'
import ClaimScorecard from './ClaimScorecard'
import EmotionBar from './EmotionBar'
import HumorBlock from './HumorBlock'
import ActionButtons from './ActionButtons'

export default function IntelCard({ data, onReanalyze }) {
  if (!data) return null

  const {
    verdict,
    reality_score,
    score_breakdown,
    claims,
    verified_claims,
    context_drift,
    key_insights,
    trust_trail,
    emotion_exploit,
    emotion_analysis,
    humor,
    sources,
    analysis_timestamp,
    _originalQuery,
    _cached_claims,
  } = data

  return (
    <div className="intel-card">
      <div className="intel-card__inner">
        {/* Manipulation Heatmap — first visual element */}
        <ClaimHeatmap
          content={_originalQuery || ''}
          emotionExploit={emotion_exploit}
        />

        {/* Verdict + Reality Score + Score Breakdown */}
        {verdict && (
          <VerdictBlock
            score={reality_score}
            verdict={verdict}
            scoreBreakdown={score_breakdown}
            verifiedClaims={verified_claims}
          />
        )}

        {/* Per-Claim Verification Scorecard (with real source links) */}
        {verified_claims && verified_claims.length > 0 && (
          <ClaimScorecard verifiedClaims={verified_claims} />
        )}

        {/* Claim Highlights (risk words in each claim) */}
        {claims && claims.length > 0 && (
          <HeatmapBlock claims={claims} />
        )}

        {/* Context Drift Warning */}
        {context_drift && context_drift.detected && (
          <ContextDrift data={context_drift} />
        )}

        {/* Key Intelligence Insights */}
        {key_insights && key_insights.length > 0 && (
          <KeyInsights items={key_insights} />
        )}

        {/* Trust Trail — real clickable source links */}
        {trust_trail && trust_trail.length > 0 && (
          <TrustTrail items={trust_trail} />
        )}

        {/* Emotion Exploitation Panel */}
        {emotion_exploit && emotion_exploit.overall_manipulation_score > 0 && (
          <EmotionExploitPanel data={emotion_exploit} />
        )}

        {/* Fallback: old Emotion Bar if no exploit data */}
        {!emotion_exploit && emotion_analysis && emotion_analysis.intensity > 0 && (
          <EmotionBar data={emotion_analysis} />
        )}

        {/* Humor Block (suppressed for sensitive topics) */}
        {humor && humor.joke && !humor.suppressed && (
          <HumorBlock data={humor} />
        )}

        {/* Sensitivity notice when humor is suppressed */}
        {humor && humor.suppressed && (
          <div className="humor-suppressed">
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>info</span>
            <span>Humor suppressed — {humor.suppressed_reason || 'sensitive content detected'}</span>
          </div>
        )}

        {/* Action Buttons */}
        <ActionButtons
          sources={sources}
          onReanalyze={() => onReanalyze(_originalQuery, _cached_claims)}
          timestamp={analysis_timestamp}
        />
      </div>
    </div>
  )
}
