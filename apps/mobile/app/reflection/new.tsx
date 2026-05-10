import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { WIZARD_STEPS } from "../../src/types";
import { createReflection, getReflection, updateReflection } from "../../src/api/reflections";
import type { CreateReflectionRequest } from "../../src/types";
import { GradientButton } from "../../src/components/GradientButton";
import { colors, radii, shadow } from "../../src/styles/theme";

export default function NewReflectionScreen() {
  const router = useRouter();
  const { edit } = useLocalSearchParams<{ edit?: string }>();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [loadingEdit, setLoadingEdit] = useState(false);
  const [loadError, setLoadError] = useState("");

  const current = WIZARD_STEPS[step];
  const value = answers[current.key] ?? "";

  useEffect(() => {
    if (!edit) return;
    setLoadingEdit(true);
    setLoadError("");
    getReflection(edit)
      .then((reflection) => {
        setAnswers({
          situation: reflection.situation,
          feelings: reflection.feelings,
          interpretation: reflection.interpretation,
          needs: reflection.needs,
          fears: reflection.fears,
          desired_outcome: reflection.desired_outcome,
          message_draft: reflection.message_draft,
        });
      })
      .catch(() => setLoadError("Could not load this reflection for editing. Check the API connection and try again."))
      .finally(() => setLoadingEdit(false));
  }, [edit]);

  async function retryLoadEdit() {
    if (!edit) return;
    setLoadingEdit(true);
    setLoadError("");
    try {
      const reflection = await getReflection(edit);
      setAnswers({
        situation: reflection.situation,
        feelings: reflection.feelings,
        interpretation: reflection.interpretation,
        needs: reflection.needs,
        fears: reflection.fears,
        desired_outcome: reflection.desired_outcome,
        message_draft: reflection.message_draft,
      });
    } catch {
      setLoadError("Could not load this reflection for editing. Check the API connection and try again.");
    } finally {
      setLoadingEdit(false);
    }
  }

  function handleNext() {
    if (!value.trim() && step < WIZARD_STEPS.length - 1) {
      // Allow empty for now (MVP), but don't advance on empty final step
    }
    setAnswers((prev) => ({ ...prev, [current.key]: value }));
    if (step < WIZARD_STEPS.length - 1) {
      setStep((s) => s + 1);
    }
  }

  function handleBack() {
    setAnswers((prev) => ({ ...prev, [current.key]: value }));
    if (step > 0) setStep((s) => s - 1);
  }

  async function handleSave() {
    setAnswers((prev) => ({ ...prev, [current.key]: value }));
    setSaving(true);
    try {
      const title =
        answers.situation?.slice(0, 40) ||
        value.slice(0, 40) ||
        "Untitled Reflection";
      const data: CreateReflectionRequest = {
        title,
        situation: answers.situation ?? "",
        feelings: answers.feelings ?? "",
        interpretation: answers.interpretation ?? "",
        needs: answers.needs ?? "",
        fears: answers.fears ?? "",
        desired_outcome: answers.desired_outcome ?? "",
        message_draft: answers.message_draft ?? "",
      };
      const reflection = edit
        ? await updateReflection(edit, data)
        : await createReflection(data);
      router.replace(`/reflection/review?reflectionId=${reflection.id}`);
    } catch {
      Alert.alert("Could not save", "Please try again.");
    } finally {
      setSaving(false);
    }
  }

  const isLast = step === WIZARD_STEPS.length - 1;
  const progress = (step + 1) / WIZARD_STEPS.length;

  if (loadingEdit) {
    return (
      <SafeAreaView style={styles.container} edges={["bottom"]}>
        <View style={styles.stateCard}>
          <Text style={styles.stateTitle}>Opening your answers</Text>
          <Text style={styles.stateText}>Loading the saved reflection so you can adjust it.</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (loadError) {
    return (
      <SafeAreaView style={styles.container} edges={["bottom"]}>
        <View style={styles.stateCard}>
          <Text style={styles.stateTitle}>Could not open this draft</Text>
          <Text style={styles.stateText}>{loadError}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={retryLoadEdit}>
            <Text style={styles.retryText}>Try again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
        {/* Progress bar */}
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${progress * 100}%` }]} />
        </View>

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.promptCard}>
            <Text style={styles.stepLabel}>
              {step + 1} of {WIZARD_STEPS.length}
            </Text>
            <Text style={styles.question}>{current.question}</Text>
            <Text style={styles.hint}>{current.hint}</Text>

            <TextInput
              style={styles.textInput}
              value={value}
              onChangeText={(text) => {
                const next = { ...answers };
                next[current.key] = text;
                setAnswers(next);
              }}
              multiline
              placeholder={current.hint}
              placeholderTextColor="#A3A3A3"
              textAlignVertical="top"
              autoFocus
            />
          </View>
        </ScrollView>

        <View style={styles.footer}>
          {step > 0 && (
            <TouchableOpacity style={styles.backButton} onPress={handleBack}>
              <Text style={styles.backButtonText}>← Back</Text>
            </TouchableOpacity>
          )}
          <View style={{ flex: 1 }} />
          <GradientButton
            label={saving ? "Saving..." : isLast ? "Save and review" : "Next"}
            onPress={isLast ? handleSave : handleNext}
            disabled={saving}
            style={styles.nextButton}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  progressBar: { height: 5, backgroundColor: colors.border, width: "100%" },
  progressFill: { height: "100%", backgroundColor: colors.accent, borderTopRightRadius: 999, borderBottomRightRadius: 999 },
  scrollContent: { padding: 24, flexGrow: 1, justifyContent: "center" },
  promptCard: { backgroundColor: colors.surfaceSoft, borderRadius: radii.card, padding: 22, borderWidth: 1, borderColor: "rgba(0,0,0,0.04)", ...shadow.card },
  stepLabel: { fontSize: 13, color: colors.textQuiet, marginBottom: 10, fontWeight: "700", textTransform: "uppercase", letterSpacing: 1 },
  question: { fontSize: 27, fontWeight: "700", color: colors.text, marginBottom: 10, lineHeight: 36, letterSpacing: 0 },
  hint: { fontSize: 15, color: colors.textMuted, marginBottom: 24, lineHeight: 23 },
  textInput: {
    backgroundColor: colors.surface,
    borderRadius: 22,
    padding: 16,
    fontSize: 16,
    color: colors.text,
    minHeight: 170,
    textAlignVertical: "top",
    borderWidth: 1,
    borderColor: colors.border,
    lineHeight: 24,
  },
  footer: { flexDirection: "row", padding: 20, gap: 12, borderTopWidth: 1, borderTopColor: colors.border, backgroundColor: colors.background },
  backButton: { paddingVertical: 16 },
  backButtonText: { fontSize: 16, color: colors.textMuted, fontWeight: "600" },
  nextButton: { minWidth: 150 },
  stateCard: { margin: 24, marginTop: 80, padding: 22, backgroundColor: colors.surfaceSoft, borderRadius: radii.card, borderWidth: 1, borderColor: "rgba(0,0,0,0.04)", ...shadow.card },
  stateTitle: { fontSize: 18, fontWeight: "700", color: colors.text, marginBottom: 8, textAlign: "center" },
  stateText: { fontSize: 14, color: colors.textMuted, lineHeight: 21, textAlign: "center" },
  retryButton: { alignSelf: "center", marginTop: 18, paddingHorizontal: 18, paddingVertical: 11, borderRadius: radii.pill, borderWidth: 1, borderColor: colors.border },
  retryText: { color: colors.text, fontSize: 14, fontWeight: "700" },
});
