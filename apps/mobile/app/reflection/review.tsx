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

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.eyebrow}>Your reflection</Text>
        <Text style={styles.header}>Read it back slowly.</Text>
        <Text style={styles.subheader}>
          Take a moment to check in with what you wrote before we generate your conversation prep.
        </Text>

        {/* What happened */}
        <View style={styles.field}>
          <Text style={styles.fieldLabel}>What's going on</Text>
          <Text style={styles.fieldValue}>{reflection.situation}</Text>
        </View>

        {/* What they want (if provided) */}
        {reflection.desired_outcome ? (
          <View style={styles.field}>
            <Text style={styles.fieldLabel}>What they want</Text>
            <Text style={styles.fieldValue}>{reflection.desired_outcome}</Text>
          </View>
        ) : null}
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.editButton}
          onPress={() => router.push(`/reflection/new?edit=${reflection.id}`)}
        >
          <Text style={styles.editButtonText}>← Edit</Text>
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
  content: { padding: 24, paddingBottom: 120 },
  eyebrow: { fontSize: 12, fontWeight: "700", color: colors.textQuiet, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 },
  header: { fontSize: 28, fontWeight: "700", color: colors.text, marginBottom: 8, letterSpacing: 0 },
  subheader: { fontSize: 15, color: colors.textMuted, marginBottom: 28, lineHeight: 23 },
  field: { marginBottom: 20 },
  fieldLabel: { fontSize: 12, fontWeight: "700", color: colors.textQuiet, textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 },
  fieldValue: { fontSize: 17, color: colors.text, lineHeight: 27, backgroundColor: colors.surfaceSoft, padding: 16, borderRadius: radii.panel, borderWidth: 1, borderColor: "rgba(0,0,0,0.04)", ...shadow.card },
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