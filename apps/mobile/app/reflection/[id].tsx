import { useRouter, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getReflection, getFeedback, updateFeedback, archiveReflection } from "../../src/api/reflections";
import type { Reflection, ReflectionFeedback } from "../../src/types";
import { GradientButton } from "../../src/components/GradientButton";
import { AuthGate } from "../../src/auth/AuthGate";
import { useAuth } from "../../src/auth/AuthContext";
import { colors, radii, shadow } from "../../src/styles/theme";

export default function ReflectionDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { loading: authLoading, isAuthenticated } = useAuth();
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [feedback, setFeedback] = useState<ReflectionFeedback | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showFollowup, setShowFollowup] = useState(false);
  const [followupScore, setFollowupScore] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!id || authLoading || !isAuthenticated) return;
    setError("");
    Promise.all([getReflection(id), getFeedback(id).catch(() => null)])
      .then(([r, fb]) => {
        setReflection(r);
        setFeedback(fb);
        // Show follow-up if feedback exists but conversation_went_better is 0
        if (fb && fb.conversation_went_better === 0) {
          setShowFollowup(true);
        }
      })
      .catch(() => setError("Could not load this reflection."))
      .finally(() => setLoading(false));
  }, [id, authLoading, isAuthenticated]);

  async function handleSubmitFollowup() {
    if (!id || !followupScore) return;
    setSubmitting(true);
    try {
      await updateFeedback(id, { conversation_went_better: followupScore });
      setShowFollowup(false);
    } catch {
      // Silent fail
    } finally {
      setSubmitting(false);
    }
  }

  function formatDate(iso: string) {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  }

  function formatStatus(status: string) {
    switch (status) {
      case "draft": return "In progress";
      case "completed": return "Plan ready";
      case "archived": return "Archived";
      default: return status;
    }
  }

  if (authLoading || !isAuthenticated) {
    return (
      <AuthGate message="Sign in to open this saved reflection.">
        <View />
      </AuthGate>
    );
  }

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={colors.text} />
      </View>
    );
  }

  if (error || !reflection) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error || "Reflection not found."}</Text>
          <TouchableOpacity onPress={() => router.replace("/(tabs)/reflections")}>
            <Text style={styles.backLink}>← Back to reflections</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const fields: { label: string; value: string }[] = [
    { label: "What happened?", value: reflection.situation },
    { label: "What are you feeling?", value: reflection.feelings },
    { label: "What story are you telling yourself?", value: reflection.interpretation },
    { label: "What do you need?", value: reflection.needs },
    { label: "What are you afraid of?", value: reflection.fears },
    { label: "What outcome do you want?", value: reflection.desired_outcome },
    { label: "What do you want to say?", value: reflection.message_draft },
  ];

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>{reflection.title || "Untitled reflection"}</Text>
          <View style={styles.metaRow}>
            <Text style={styles.date}>{formatDate(reflection.created_at)}</Text>
            <Text style={styles.statusBadge}>{formatStatus(reflection.status)}</Text>
          </View>
        </View>

        {/* Follow-up prompt */}
        {showFollowup && (
          <View style={styles.followupBanner}>
            <Text style={styles.followupTitle}>Did the conversation go better?</Text>
            <Text style={styles.followupSubtitle}>After you had the conversation, how did it go?</Text>
            <View style={styles.scoreRow}>
              {[
                { label: "No", value: 1 },
                { label: "Somewhat", value: 2 },
                { label: "Yes", value: 3 },
              ].map(({ label, value }) => (
                <TouchableOpacity
                  key={value}
                  style={[styles.scoreBtn, followupScore === value && styles.scoreBtnSelected]}
                  onPress={() => setFollowupScore(value)}
                >
                  <Text style={[styles.scoreBtnText, followupScore === value && styles.scoreBtnTextSelected]}>{label}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <GradientButton
              label="Submit"
              onPress={handleSubmitFollowup}
              disabled={!followupScore || submitting}
            />
          </View>
        )}

        {/* Reflection fields */}
        {fields
          .filter((f) => f.value)
          .map((field) => (
            <View key={field.label} style={styles.fieldBlock}>
              <Text style={styles.fieldLabel}>{field.label}</Text>
              <Text style={styles.fieldValue}>{field.value}</Text>
            </View>
          ))}
      </ScrollView>

      {/* Actions */}
      <View style={styles.footer}>
        {reflection.status === "draft" && (
          <GradientButton
            label="Continue →"
            onPress={() => router.push(`/reflection/plan?reflectionId=${reflection.id}`)}
          />
        )}
        {reflection.status === "completed" && !showFollowup && (
          <GradientButton
            label="View plan"
            onPress={() => router.push(`/reflection/plan?reflectionId=${reflection.id}`)}
          />
        )}
        <TouchableOpacity
          style={styles.archiveBtn}
          onPress={() =>
            archiveReflection(reflection.id)
              .then(() => router.replace("/(tabs)/reflections"))
              .catch(() => {})
          }
        >
          <Text style={styles.archiveText}>Archive this reflection</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  loading: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.background },
  errorContainer: { flex: 1, justifyContent: "center", alignItems: "center", padding: 32 },
  errorText: { fontSize: 16, color: colors.textMuted, marginBottom: 16 },
  backLink: { fontSize: 16, color: colors.accent, fontWeight: "600" },
  content: { padding: 24, paddingBottom: 120 },
  header: { marginBottom: 28 },
  title: { fontSize: 24, fontWeight: "700", color: colors.text, marginBottom: 8 },
  metaRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  date: { fontSize: 14, color: colors.textMuted },
  statusBadge: { fontSize: 12, fontWeight: "600", color: colors.accent, backgroundColor: "rgba(180,100,50,0.08)", paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  followupBanner: { backgroundColor: colors.surfaceSoft, borderRadius: radii.card, padding: 20, marginBottom: 24, borderWidth: 1, borderColor: colors.border },
  followupTitle: { fontSize: 18, fontWeight: "700", color: colors.text, marginBottom: 4 },
  followupSubtitle: { fontSize: 14, color: colors.textMuted, marginBottom: 16 },
  scoreRow: { flexDirection: "row", gap: 12, marginBottom: 20 },
  scoreBtn: { flex: 1, paddingVertical: 12, borderRadius: radii.card, borderWidth: 1.5, borderColor: colors.border, backgroundColor: colors.surface, alignItems: "center" },
  scoreBtnSelected: { borderColor: colors.accent, backgroundColor: "rgba(180,100,50,0.08)" },
  scoreBtnText: { fontSize: 14, fontWeight: "600", color: colors.textMuted },
  scoreBtnTextSelected: { color: colors.accent },
  fieldBlock: { marginBottom: 20 },
  fieldLabel: { fontSize: 12, fontWeight: "700", color: colors.textQuiet, textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 },
  fieldValue: { fontSize: 16, color: colors.text, lineHeight: 24 },
  footer: { position: "absolute", bottom: 0, left: 0, right: 0, padding: 20, borderTopWidth: 1, borderTopColor: colors.border, backgroundColor: colors.background, gap: 12 },
  archiveBtn: { alignItems: "center", padding: 8 },
  archiveText: { fontSize: 14, color: colors.textMuted },
});
