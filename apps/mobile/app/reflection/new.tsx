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
import { createReflection, getReflection, updateReflection } from "../../src/api/reflections";
import type { CreateReflectionRequest } from "../../src/types";
import { GradientButton } from "../../src/components/GradientButton";
import { AuthGate } from "../../src/auth/AuthGate";
import { useAuth } from "../../src/auth/AuthContext";
import { colors, radii, shadow } from "../../src/styles/theme";

export default function NewReflectionScreen() {
  const router = useRouter();
  const { edit } = useLocalSearchParams<{ edit?: string }>();
  const { loading: authLoading, isAuthenticated } = useAuth();
  const [saving, setSaving] = useState(false);
  const [loadingEdit, setLoadingEdit] = useState(false);
  const [loadError, setLoadError] = useState("");

  // Simplified: two fields only
  const [situation, setSituation] = useState("");
  const [desiredOutcome, setDesiredOutcome] = useState("");

  useEffect(() => {
    if (!edit || authLoading || !isAuthenticated) return;
    setLoadingEdit(true);
    setLoadError("");
    getReflection(edit)
      .then((reflection) => {
        setSituation(reflection.situation || "");
        setDesiredOutcome(reflection.desired_outcome || "");
      })
      .catch(() => setLoadError("Could not load this reflection for editing. Check the API connection and try again."))
      .finally(() => setLoadingEdit(false));
  }, [edit, authLoading, isAuthenticated]);

  async function retryLoadEdit() {
    if (!edit) return;
    setLoadingEdit(true);
    setLoadError("");
    try {
      const reflection = await getReflection(edit);
      setSituation(reflection.situation || "");
      setDesiredOutcome(reflection.desired_outcome || "");
    } catch {
      setLoadError("Could not load this reflection for editing. Check the API connection and try again.");
    } finally {
      setLoadingEdit(false);
    }
  }

  async function handleSubmit() {
    const trimmedSituation = situation.trim();
    if (!trimmedSituation) return;

    setSaving(true);
    try {
      const title = trimmedSituation.slice(0, 80) || "Untitled Reflection";
      const data: CreateReflectionRequest = {
        title,
        situation: trimmedSituation,
        desired_outcome: desiredOutcome.trim(),
        // Legacy fields kept empty for simplified input
        feelings: "",
        interpretation: "",
        needs: "",
        fears: "",
        message_draft: "",
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

  if (authLoading || !isAuthenticated) {
    return (
      <AuthGate message="Sign in to create and save Feltabout reflections.">
        <View />
      </AuthGate>
    );
  }

  if (loadingEdit) {
    return (
      <SafeAreaView style={styles.container} edges={["bottom"]}>
        <View style={styles.stateCard}>
          <Text style={styles.stateTitle}>Opening your reflection</Text>
          <Text style={styles.stateText}>Loading your saved work.</Text>
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
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.headerCard}>
            <Text style={styles.mainPrompt}>Tell me what's going on.</Text>
            <Text style={styles.subPrompt}>Say it messy. We'll find the clarity.</Text>
          </View>

          {/* Main input */}
          <View style={styles.inputCard}>
            <TextInput
              style={styles.mainInput}
              value={situation}
              onChangeText={setSituation}
              multiline
              placeholder="Something happened, or it's been building up. Just get it out..."
              placeholderTextColor="#A3A3A3"
              textAlignVertical="top"
              autoFocus
            />
          </View>

          {/* Optional: what do you want */}
          <View style={styles.optionalCard}>
            <Text style={styles.optionalLabel}>What do you want from this conversation? (optional)</Text>
            <TextInput
              style={styles.secondaryInput}
              value={desiredOutcome}
              onChangeText={setDesiredOutcome}
              multiline
              placeholder="e.g. I want us to understand each other better, not fix everything tonight"
              placeholderTextColor="#A3A3A3"
              textAlignVertical="top"
            />
          </View>
        </ScrollView>

        <View style={styles.footer}>
          <GradientButton
            label={saving ? "Finding the words..." : "Find the words"}
            onPress={handleSubmit}
            disabled={saving || !situation.trim()}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  scrollContent: { padding: 24, paddingBottom: 120 },
  headerCard: { marginBottom: 20 },
  mainPrompt: { fontSize: 28, fontWeight: "700", color: colors.text, marginBottom: 8, lineHeight: 36 },
  subPrompt: { fontSize: 16, color: colors.textMuted, lineHeight: 24 },
  inputCard: { marginBottom: 20 },
  mainInput: {
    backgroundColor: colors.surface,
    borderRadius: 22,
    padding: 18,
    fontSize: 17,
    color: colors.text,
    minHeight: 180,
    textAlignVertical: "top",
    borderWidth: 1,
    borderColor: colors.border,
    lineHeight: 26,
  },
  optionalCard: {},
  optionalLabel: { fontSize: 14, fontWeight: "600", color: colors.textMuted, marginBottom: 10 },
  secondaryInput: {
    backgroundColor: colors.surface,
    borderRadius: 18,
    padding: 16,
    fontSize: 16,
    color: colors.text,
    minHeight: 80,
    textAlignVertical: "top",
    borderWidth: 1,
    borderColor: colors.border,
    lineHeight: 24,
  },
  footer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.background
  },
  stateCard: { margin: 24, marginTop: 80, padding: 22, backgroundColor: colors.surfaceSoft, borderRadius: radii.card, borderWidth: 1, borderColor: "rgba(0,0,0,0.04)", ...shadow.card },
  stateTitle: { fontSize: 18, fontWeight: "700", color: colors.text, marginBottom: 8, textAlign: "center" },
  stateText: { fontSize: 14, color: colors.textMuted, lineHeight: 21, textAlign: "center" },
  retryButton: { alignSelf: "center", marginTop: 18, paddingHorizontal: 18, paddingVertical: 11, borderRadius: radii.pill, borderWidth: 1, borderColor: colors.border },
  retryText: { color: colors.text, fontSize: 14, fontWeight: "700" },
});
