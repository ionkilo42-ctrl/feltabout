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
import { colors, radii, shadow } from "../../src/styles/theme";

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
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  // Feedback state
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [preparedScore, setPreparedScore] = useState(0);
  const [reactiveScore, setReactiveScore] = useState(0);
  const [helpfulText, setHelpfulText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  useEffect(() => {
    if (!reflectionId) return;
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
  }, [reflectionId]);

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

  function handleDone() {
    if (!feedbackSubmitted) {
      setShowFeedbackModal(true);
    } else {
      router.replace("/(tabs)/reflections");
    }
  }

  // ─── Render states ─────────────────────────────────────────────────────────

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={colors.text} />
        <Text style={styles.generatingText}>Loading reflection</Text>
        <Text style={styles.generatingHint}>Checking whether a plan already exists.</Text>
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
          <Text style={styles.preText}>Based on your reflection, feltabout will help you:</Text>
          <View style={styles.preList}>
            {[
              "Summarize your emotional landscape",
              "Clarify your underlying needs",
              "Identify possible assumptions",
              "Suggest a calm conversation opener",
              "Offer follow-up questions",
              "Provide a repair-oriented closing",
            ].map((item, i) => (
              <Text key={i} style={styles.preListItem}>✓ {item}</Text>
            ))}
          </View>
          <GradientButton label="Generate plan" onPress={handleGenerate} />
          <TouchableOpacity onPress={() => router.back()}>
            <Text style={styles.reviewText}>← Review my answers</Text>
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
        <Text style={styles.generatingText}>Preparing your plan...</Text>
        <Text style={styles.generatingHint}>This may take a few moments.</Text>
      </View>
    );
  }

  // Display plan
  const output = result?.output;
  if (!output) return null;

  const sections: { title: string; content: string; icon: string }[] = [
    { title: "Emotional Summary", content: output.emotional_summary, icon: "◉" },
    { title: "Your Needs", content: output.needs_summary, icon: "◉" },
    { title: "Possible Assumptions", content: output.assumptions, icon: "◉" },
    { title: "Gentle Reframe", content: output.reframe, icon: "◉" },
    { title: "What to Avoid", content: output.avoid_saying, icon: "◉" },
    { title: "Conversation Opener", content: output.conversation_opener, icon: "◉" },
    { title: "Follow-Up Questions", content: output.followup_questions, icon: "◉" },
    { title: "Repair Statement", content: output.repair_statement, icon: "◉" },
  ];

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScrollView contentContainerStyle={styles.planContent}>
        <View style={styles.planHeader}>
          <Text style={styles.planTitle}>Your Conversation Plan</Text>
          <Text style={styles.planSubtitle}>Use this as a guide — adapt it to your own voice.</Text>
        </View>

        {sections.map((section) =>
          section.content ? (
            <View key={section.title} style={styles.section}>
              <Text style={styles.sectionIcon}>{section.icon}</Text>
              <Text style={styles.sectionTitle}>{section.title}</Text>
              <View style={styles.sectionBody}>
                {formatPlanContent(section.content).map((line, index) => (
                  <Text key={`${section.title}-${index}`} style={styles.sectionContent}>{line}</Text>
                ))}
              </View>
            </View>
          ) : null
        )}
      </ScrollView>

      <View style={styles.planFooter}>
        <GradientButton
          label={feedbackSubmitted ? "Done" : "I'm done — share feedback"}
          onPress={handleDone}
        />
      </View>

      {/* Feedback Modal */}
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

            {/* Question 1 */}
            <Text style={styles.questionText}>Do you feel more prepared for the conversation?</Text>
            <View style={styles.scoreRow}>
              <ScoreOption label="No" value={1} selected={preparedScore === 1} onPress={() => setPreparedScore(1)} />
              <ScoreOption label="Somewhat" value={2} selected={preparedScore === 2} onPress={() => setPreparedScore(2)} />
              <ScoreOption label="Yes" value={3} selected={preparedScore === 3} onPress={() => setPreparedScore(3)} />
            </View>

            {/* Question 2 */}
            <Text style={styles.questionText}>Do you feel less reactive than before?</Text>
            <View style={styles.scoreRow}>
              <ScoreOption label="No" value={1} selected={reactiveScore === 1} onPress={() => setReactiveScore(1)} />
              <ScoreOption label="Somewhat" value={2} selected={reactiveScore === 2} onPress={() => setReactiveScore(2)} />
              <ScoreOption label="Yes" value={3} selected={reactiveScore === 3} onPress={() => setReactiveScore(3)} />
            </View>

            {/* Optional text */}
            <Text style={styles.questionText}>What was most helpful? (optional)</Text>
            <TextInput
              style={styles.textInput}
              placeholder="Share what helped..."
              placeholderTextColor={colors.textMuted}
              value={helpfulText}
              onChangeText={setHelpfulText}
              multiline
            />

            {/* Actions */}
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.skipButton}
                onPress={() => {
                  setShowFeedbackModal(false);
                  router.replace("/(tabs)/reflections");
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
  preList: { gap: 10, marginBottom: 32 },
  preListItem: { fontSize: 15, color: colors.text, lineHeight: 22 },
  reviewText: { textAlign: "center", color: colors.textMuted, fontSize: 15, marginTop: 20, fontWeight: "600" },
  planContent: { padding: 24, paddingBottom: 100 },
  planHeader: { marginBottom: 28 },
  planTitle: { fontSize: 27, fontWeight: "700", color: colors.text, marginBottom: 8, letterSpacing: 0 },
  planSubtitle: { fontSize: 15, color: colors.textMuted, lineHeight: 23 },
  section: { marginBottom: 16, backgroundColor: colors.surfaceSoft, padding: 18, borderRadius: radii.card, borderWidth: 1, borderColor: "rgba(0,0,0,0.04)", ...shadow.card },
  sectionIcon: { color: colors.accent, fontSize: 18, marginBottom: 8 },
  sectionTitle: { fontSize: 12, fontWeight: "700", color: colors.textQuiet, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 },
  sectionBody: { gap: 8 },
  sectionContent: { fontSize: 16, color: colors.text, lineHeight: 25 },
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
});