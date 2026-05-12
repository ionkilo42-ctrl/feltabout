import { useRouter, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  TextInput,
  Modal,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getReflection, generatePlan, submitFeedback as apiSubmitFeedback, getFeedback as apiGetFeedback, updateFeedback as apiUpdateFeedback } from "../../src/api/reflections";
import type { Reflection, GenerateResponse, ReflectionFeedback } from "../../src/types";
import { GradientButton } from "../../src/components/GradientButton";
import { AuthGate } from "../../src/auth/AuthGate";
import { useAuth } from "../../src/auth/AuthContext";
import { colors, radii, shadow } from "../../src/styles/theme";

// ─── How Did It Go Options ────────────────────────────────────────────────────

const HOW_DID_IT_GO_OPTIONS = [
  { label: "Better than expected", value: 1 },
  { label: "About the same", value: 2 },
  { label: "Worse", value: 3 },
  { label: "I didn't have the conversation", value: 4 },
];

// ─── Score Option ─────────────────────────────────────────────────────────────

function ScoreOption({
  label,
  value,
  selected,
  onPress,
}: {
  label: string;
  value: number;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      style={[styles.scoreOption, selected && styles.scoreOptionSelected]}
      onPress={onPress}
    >
      <Text style={[styles.scoreLabel, selected && styles.scoreLabelSelected]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

// ─── Main Plan Screen ─────────────────────────────────────────────────────────

export default function PlanScreen() {
  const router = useRouter();
  const { reflectionId } = useLocalSearchParams<{ reflectionId: string }>();
  const { loading: authLoading, isAuthenticated } = useAuth();
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  // Show details toggle
  const [showDetails, setShowDetails] = useState(false);

  // Feedback state
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [preparedScore, setPreparedScore] = useState(0);
  const [reactiveScore, setReactiveScore] = useState(0);
  const [helpfulText, setHelpfulText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  // "How did it go" state (for follow-up)
  const [showFollowupModal, setShowFollowupModal] = useState(false);
  const [howDidItGo, setHowDidItGo] = useState(0);
  const [whatHappened, setWhatHappened] = useState("");

  useEffect(() => {
    if (!reflectionId || authLoading || !isAuthenticated) return;
    setError("");
    getReflection(reflectionId)
      .then((r) => {
        setReflection(r);
        if (r.output) {
          setResult({
            is_crisis: false,
            severity: "none",
            message: "Your conversation plan is ready.",
            resources: [],
            output: r.output,
          });
        }
        // Check if feedback already exists
        if (r.id) {
          apiGetFeedback(r.id)
            .then((fb) => {
              if (fb) {
                setFeedbackSubmitted(true);
              }
            })
            .catch(() => {});
        }
      })
      .catch(() => setError("Could not load this reflection. Check the API connection and try again."))
      .finally(() => setLoading(false));
  }, [reflectionId, authLoading, isAuthenticated]);

  async function handleGenerate() {
    if (!reflectionId) return;
    setGenerating(true);
    setError("");
    try {
      const response = await generatePlan(reflectionId);
      setResult(response);
      const updated = await getReflection(reflectionId);
      setReflection(updated);
    } catch {
      setError("Could not generate the plan. The reflection is still saved; try again when the API is reachable.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleSubmitFeedback() {
    if (!reflectionId || !preparedScore || !reactiveScore) return;
    setSubmitting(true);
    try {
      await apiSubmitFeedback(reflectionId, {
        prepared_score: preparedScore,
        less_reactive_score: reactiveScore,
        helpful_text: helpfulText,
      });
      setFeedbackSubmitted(true);
      setShowFeedbackModal(false);
    } catch {
      // Silently fail — user can try again
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmitFollowup() {
    if (!reflectionId) return;
    setSubmitting(true);
    try {
      await apiUpdateFeedback(reflectionId, {
        how_did_it_go: howDidItGo,
        what_happened: whatHappened,
      });
      setShowFollowupModal(false);
      router.replace("/(tabs)/reflections");
    } catch {
      // Silently fail
    } finally {
      setSubmitting(false);
    }
  }

  function handleDone() {
    if (!feedbackSubmitted) {
      setShowFeedbackModal(true);
    } else {
      // Show follow-up: "How did it go?"
      setShowFollowupModal(true);
    }
  }

  // ─── Render states ─────────────────────────────────────────────────────────

  if (authLoading || !isAuthenticated) {
    return (
      <AuthGate message="Sign in to generate or view conversation plans.">
        <View />
      </AuthGate>
    );
  }

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={colors.text} />
        <Text style={styles.generatingText}>Loading reflection</Text>
      </View>
    );
  }

  if (error && !generating) {
    return (
      <SafeAreaView style={styles.container} edges={["bottom"]}>
        <View style={styles.preGenerate}>
          <Text style={styles.preTitle}>Something did not connect</Text>
          <Text style={styles.preText}>{error}</Text>
          <GradientButton
            label={reflection ? "Try generating again" : "Try again"}
            onPress={reflection ? handleGenerate : () => router.replace("/(tabs)/reflections")}
          />
          <TouchableOpacity onPress={() => router.replace("/(tabs)/reflections")}>
            <Text style={styles.reviewText}>Back to reflections</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Crisis response
  if (result?.is_crisis) {
    return (
      <SafeAreaView style={styles.container} edges={["bottom"]}>
        <ScrollView contentContainerStyle={styles.crisisContent}>
          <Text style={styles.crisisTitle}>Support Resources</Text>
          <Text style={styles.crisisMessage}>{result.message}</Text>
          {result.resources.map((resource, i) => (
            <View key={i} style={styles.resourceItem}>
              <Text style={styles.resourceText}>{resource}</Text>
            </View>
          ))}
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.replace("/(tabs)/reflections")}
          >
            <Text style={styles.backButtonText}>← Back to Reflections</Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Not yet generated
  if (!result && !generating) {
    return (
      <SafeAreaView style={styles.container} edges={["bottom"]}>
        <View style={styles.preGenerate}>
          <Text style={styles.preTitle}>Ready to prepare?</Text>
          <Text style={styles.preText}>Tell me what happened, and I'll help you find the right words.</Text>
          <GradientButton label="Generate plan" onPress={handleGenerate} />
          <TouchableOpacity onPress={() => router.back()}>
            <Text style={styles.reviewText}>← Review my reflection</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Generating
  if (generating) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#2D2D2D" />
        <Text style={styles.generatingText}>Finding the right words</Text>
        <Text style={styles.generatingHint}>One moment...</Text>
      </View>
    );
  }

  // Display plan
  const output = result?.output;
  if (!output) return null;

  // Primary output: simple_opener
  const simpleOpener = output.simple_opener || output.conversation_opener || "";

  // Full details (collapsible)
  const sections = [
    { title: "What you're carrying", content: output.emotional_summary, key: "emotional_summary" },
    { title: "What you need", content: output.needs_summary, key: "needs_summary" },
    { title: "Assumptions to check", content: output.assumptions, key: "assumptions" },
    { title: "A clearer frame", content: output.reframe, key: "reframe" },
    { title: "What to avoid", content: output.avoid_saying, key: "avoid_saying" },
    { title: "Follow-up questions", content: output.followup_questions, key: "followup_questions" },
    { title: "Closing statement", content: output.repair_statement, key: "repair_statement" },
  ].filter(s => s.content);

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScrollView contentContainerStyle={styles.planContent}>
        {/* Primary opener */}
        {simpleOpener && (
          <View style={styles.openerCard}>
            <Text style={styles.openerLabel}>One thing you could say</Text>
            <Text style={styles.openerText}>{simpleOpener}</Text>
          </View>
        )}

        {/* Expandable details */}
        <TouchableOpacity
          style={styles.detailsToggle}
          onPress={() => setShowDetails(!showDetails)}
        >
          <Text style={styles.detailsToggleText}>
            {showDetails ? "Hide details" : "See full details"}
          </Text>
        </TouchableOpacity>

        {showDetails && (
          <View style={styles.detailsSection}>
            {sections.map((section) => (
              <View key={section.key} style={styles.section}>
                <Text style={styles.sectionTitle}>{section.title}</Text>
                <Text style={styles.sectionContent}>{section.content}</Text>
              </View>
            ))}
          </View>
        )}
      </ScrollView>

      <View style={styles.planFooter}>
        <GradientButton
          label={feedbackSubmitted ? "Done" : "I'm done — share feedback"}
          onPress={handleDone}
        />
      </View>

      {/* Initial Feedback Modal */}
      <Modal
        visible={showFeedbackModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowFeedbackModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Before you go</Text>
            <Text style={styles.modalSubtitle}>Quick feedback to help us improve.</Text>

            <Text style={styles.questionText}>Do you feel more prepared for the conversation?</Text>
            <View style={styles.scoreRow}>
              <ScoreOption label="No" value={1} selected={preparedScore === 1} onPress={() => setPreparedScore(1)} />
              <ScoreOption label="Somewhat" value={2} selected={preparedScore === 2} onPress={() => setPreparedScore(2)} />
              <ScoreOption label="Yes" value={3} selected={preparedScore === 3} onPress={() => setPreparedScore(3)} />
            </View>

            <Text style={styles.questionText}>Do you feel less reactive than before?</Text>
            <View style={styles.scoreRow}>
              <ScoreOption label="No" value={1} selected={reactiveScore === 1} onPress={() => setReactiveScore(1)} />
              <ScoreOption label="Somewhat" value={2} selected={reactiveScore === 2} onPress={() => setReactiveScore(2)} />
              <ScoreOption label="Yes" value={3} selected={reactiveScore === 3} onPress={() => setReactiveScore(3)} />
            </View>

            <Text style={styles.questionText}>What was most helpful? (optional)</Text>
            <TextInput
              style={styles.textInput}
              placeholder="Share what helped..."
              placeholderTextColor={colors.textMuted}
              value={helpfulText}
              onChangeText={setHelpfulText}
              multiline
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.skipButton}
                onPress={() => {
                  setShowFeedbackModal(false);
                  setShowFollowupModal(true);
                }}
              >
                <Text style={styles.skipText}>Skip</Text>
              </TouchableOpacity>
              <GradientButton
                label="Submit"
                onPress={handleSubmitFeedback}
                disabled={!preparedScore || !reactiveScore || submitting}
              />
            </View>
          </View>
        </View>
      </Modal>

      {/* Follow-up: "How did it go?" Modal */}
      <Modal
        visible={showFollowupModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowFollowupModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>How did it go?</Text>
            <Text style={styles.modalSubtitle}>After you had the conversation, how did it go?</Text>

            <View style={styles.howDidItGoOptions}>
              {HOW_DID_IT_GO_OPTIONS.map((option) => (
                <TouchableOpacity
                  key={option.value}
                  style={[
                    styles.howDidItGoOption,
                    howDidItGo === option.value && styles.howDidItGoOptionSelected,
                  ]}
                  onPress={() => setHowDidItGo(option.value)}
                >
                  <Text
                    style={[
                      styles.howDidItGoOptionText,
                      howDidItGo === option.value && styles.howDidItGoOptionTextSelected,
                    ]}
                  >
                    {option.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.questionText}>What happened? (optional)</Text>
            <TextInput
              style={styles.textInput}
              placeholder="Tell me how it went..."
              placeholderTextColor={colors.textMuted}
              value={whatHappened}
              onChangeText={setWhatHappened}
              multiline
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.skipButton}
                onPress={() => {
                  setShowFollowupModal(false);
                  router.replace("/(tabs)/reflections");
                }}
              >
                <Text style={styles.skipText}>Skip</Text>
              </TouchableOpacity>
              <GradientButton
                label="Done"
                onPress={handleSubmitFollowup}
                disabled={submitting}
              />
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function formatPlanContent(content: string): string[] {
  return content
    .replace(/(\d+\.\s)/g, "\n$1")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  loading: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.background, gap: 16 },
  generatingText: { fontSize: 18, fontWeight: "700", color: colors.text },
  generatingHint: { fontSize: 14, color: colors.textMuted },
  crisisContent: { padding: 24 },
  crisisTitle: { fontSize: 25, fontWeight: "700", color: colors.text, marginBottom: 16 },
  crisisMessage: { fontSize: 16, color: colors.textMuted, lineHeight: 24, marginBottom: 24 },
  resourceItem: { backgroundColor: colors.surface, padding: 16, borderRadius: radii.panel, marginBottom: 12, borderWidth: 1, borderColor: colors.border },
  resourceText: { fontSize: 15, color: colors.text, lineHeight: 22 },
  backButton: { marginTop: 24 },
  backButtonText: { fontSize: 16, color: colors.textMuted, fontWeight: "600" },
  preGenerate: { flex: 1, justifyContent: "center", padding: 32 },
  preTitle: { fontSize: 28, fontWeight: "700", color: colors.text, marginBottom: 12 },
  preText: { fontSize: 16, color: colors.textMuted, marginBottom: 20, lineHeight: 24 },
  reviewText: { textAlign: "center", color: colors.textMuted, fontSize: 15, marginTop: 20, fontWeight: "600" },
  planContent: { padding: 24, paddingBottom: 100 },
  // Primary opener
  openerCard: { backgroundColor: colors.surface, borderRadius: 20, padding: 22, borderWidth: 1, borderColor: colors.border, marginBottom: 20 },
  openerLabel: { fontSize: 12, fontWeight: "700", color: colors.accent, textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 },
  openerText: { fontSize: 20, fontWeight: "500", color: colors.text, lineHeight: 30 },
  // Details toggle
  detailsToggle: { paddingVertical: 12, marginBottom: 8 },
  detailsToggleText: { fontSize: 15, color: colors.textMuted, fontWeight: "600" },
  // Details section
  detailsSection: { marginTop: 8 },
  section: { backgroundColor: colors.surfaceSoft, padding: 16, borderRadius: radii.card, borderWidth: 1, borderColor: "rgba(0,0,0,0.04)", marginBottom: 12, ...shadow.card },
  sectionTitle: { fontSize: 12, fontWeight: "700", color: colors.textQuiet, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 },
  sectionContent: { fontSize: 15, color: colors.text, lineHeight: 24 },
  // Footer
  planFooter: { position: "absolute", bottom: 0, left: 0, right: 0, padding: 20, borderTopWidth: 1, borderTopColor: colors.border, backgroundColor: colors.background },
  // Modal
  modalOverlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end" },
  modalContent: { backgroundColor: colors.background, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24, paddingBottom: 40 },
  modalTitle: { fontSize: 22, fontWeight: "700", color: colors.text, marginBottom: 4 },
  modalSubtitle: { fontSize: 15, color: colors.textMuted, marginBottom: 28 },
  questionText: { fontSize: 16, fontWeight: "600", color: colors.text, marginBottom: 12, marginTop: 20 },
  scoreRow: { flexDirection: "row", gap: 12, marginBottom: 8 },
  scoreOption: { flex: 1, paddingVertical: 12, paddingHorizontal: 16, borderRadius: radii.card, borderWidth: 1.5, borderColor: colors.border, backgroundColor: colors.surface, alignItems: "center" },
  scoreOptionSelected: { borderColor: colors.accent, backgroundColor: "rgba(180,100,50,0.08)" },
  scoreLabel: { fontSize: 14, fontWeight: "600", color: colors.textMuted },
  scoreLabelSelected: { color: colors.accent },
  textInput: { borderWidth: 1, borderColor: colors.border, borderRadius: radii.card, padding: 14, fontSize: 15, color: colors.text, backgroundColor: colors.surface, minHeight: 80, textAlignVertical: "top" },
  modalActions: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 28, gap: 16 },
  skipButton: { paddingVertical: 16 },
  skipText: { fontSize: 16, color: colors.textMuted, fontWeight: "600" },
  // How did it go options
  howDidItGoOptions: { gap: 10, marginBottom: 20 },
  howDidItGoOption: { paddingVertical: 14, paddingHorizontal: 18, borderRadius: 14, borderWidth: 1.5, borderColor: colors.border, backgroundColor: colors.surface },
  howDidItGoOptionSelected: { borderColor: colors.accent, backgroundColor: "rgba(180,100,50,0.08)" },
  howDidItGoOptionText: { fontSize: 15, fontWeight: "600", color: colors.textMuted, textAlign: "center" },
  howDidItGoOptionTextSelected: { color: colors.accent },
});