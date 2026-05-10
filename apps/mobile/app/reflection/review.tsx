import { useRouter, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getReflection } from "../../src/api/reflections";
import type { Reflection } from "../../src/types";
import { GradientButton } from "../../src/components/GradientButton";
import { AuthGate } from "../../src/auth/AuthGate";
import { useAuth } from "../../src/auth/AuthContext";
import { colors, radii, shadow } from "../../src/styles/theme";

export default function ReviewScreen() {
  const router = useRouter();
  const { reflectionId } = useLocalSearchParams<{ reflectionId: string }>();
  const { loading: authLoading, isAuthenticated } = useAuth();
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!reflectionId || authLoading || !isAuthenticated) return;
    getReflection(reflectionId)
      .then(setReflection)
      .catch(() => Alert.alert("Error", "Could not load reflection."))
      .finally(() => setLoading(false));
  }, [reflectionId, authLoading, isAuthenticated]);

  if (authLoading || !isAuthenticated) {
    return (
      <AuthGate message="Sign in to review your saved reflection.">
        <View />
      </AuthGate>
    );
  }

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#2D2D2D" />
      </View>
    );
  }

  if (!reflection) {
    return (
      <View style={styles.loading}>
        <Text style={{ color: "#888" }}>Reflection not found.</Text>
      </View>
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
        <Text style={styles.eyebrow}>Review</Text>
        <Text style={styles.header}>Read it back slowly.</Text>
        <Text style={styles.subheader}>
          Take a moment to read through your answers before generating a conversation plan.
        </Text>

        {fields.map(
          (field) =>
            field.value ? (
              <View key={field.label} style={styles.field}>
                <Text style={styles.fieldLabel}>{field.label}</Text>
                <Text style={styles.fieldValue}>{field.value}</Text>
              </View>
            ) : null
        )}
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.editButton}
          onPress={() => router.push(`/reflection/new?edit=${reflection.id}`)}
        >
          <Text style={styles.editButtonText}>← Edit Answers</Text>
        </TouchableOpacity>
        <GradientButton
          label="Generate plan"
          onPress={() => router.push(`/reflection/plan?reflectionId=${reflection.id}`)}
          style={styles.generateButton}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  loading: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.background },
  content: { padding: 24, paddingBottom: 100 },
  eyebrow: { fontSize: 12, fontWeight: "700", color: colors.textQuiet, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 },
  header: { fontSize: 28, fontWeight: "700", color: colors.text, marginBottom: 8, letterSpacing: 0 },
  subheader: { fontSize: 15, color: colors.textMuted, marginBottom: 28, lineHeight: 23 },
  field: { marginBottom: 20 },
  fieldLabel: { fontSize: 12, fontWeight: "700", color: colors.textQuiet, textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 },
  fieldValue: { fontSize: 16, color: colors.text, lineHeight: 25, backgroundColor: colors.surfaceSoft, padding: 16, borderRadius: radii.panel, borderWidth: 1, borderColor: "rgba(0,0,0,0.04)", ...shadow.card },
  footer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    padding: 20,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.background,
  },
  editButton: { paddingVertical: 14 },
  editButtonText: { fontSize: 16, color: colors.textMuted, fontWeight: "600" },
  generateButton: { flex: 1 },
});
