import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { listReflections, deleteReflection, archiveReflection } from "../../src/api/reflections";
import type { Reflection } from "../../src/types";
import { colors, radii, shadow } from "../../src/styles/theme";

export default function ReflectionsScreen() {
  const router = useRouter();
  const [reflections, setReflections] = useState<Reflection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await listReflections();
      setReflections(data);
    } catch {
      setError("Could not load reflections. Check that the Feltabout API is running, then try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleDelete(id: string) {
    if (confirmDeleteId !== id) {
      setConfirmDeleteId(id);
      return;
    }

    setBusyId(id);
    try {
      await deleteReflection(id);
      setReflections((prev) => prev.filter((r) => r.id !== id));
      setConfirmDeleteId(null);
    } catch {
      Alert.alert("Could not delete", "The reflection is still saved. Please try again.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleArchive(id: string) {
    setBusyId(id);
    try {
      await archiveReflection(id);
      setReflections((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: "archived" as const } : r))
      );
    } catch {
      Alert.alert("Could not archive", "Please try again.");
    } finally {
      setBusyId(null);
    }
  }

  function renderItem({ item }: { item: Reflection }) {
    const date = new Date(item.created_at).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => router.push(`/reflection/${item.id}`)}
        activeOpacity={0.7}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle} numberOfLines={1}>
            {item.title || "Untitled Reflection"}
          </Text>
          <StatusBadge status={item.status} />
        </View>
        {item.situation ? (
          <Text style={styles.cardSituation} numberOfLines={2}>
            {item.situation}
          </Text>
        ) : null}
        <Text style={styles.cardDate}>{date}</Text>
        <View style={styles.cardActions}>
          <TouchableOpacity
            onPress={() => router.push(`/reflection/${item.id}`)}
          >
            <Text style={styles.actionText}>View</Text>
          </TouchableOpacity>
          {item.status === "completed" && (
            <TouchableOpacity
              onPress={() => router.push(`/reflection/plan?reflectionId=${item.id}`)}
            >
              <Text style={styles.actionText}>Plan</Text>
            </TouchableOpacity>
          )}
          {item.status !== "archived" && (
            <TouchableOpacity onPress={() => handleArchive(item.id)} disabled={busyId === item.id}>
              <Text style={[styles.actionText, { color: "#A0A0A0" }]}>
                {busyId === item.id ? "Saving..." : "Archive"}
              </Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity onPress={() => handleDelete(item.id)} disabled={busyId === item.id}>
            <Text style={[styles.actionText, { color: "#D9534F" }]}>
              {busyId === item.id
                ? "Deleting..."
                : confirmDeleteId === item.id
                  ? "Confirm delete"
                  : "Delete"}
            </Text>
          </TouchableOpacity>
          {confirmDeleteId === item.id && busyId !== item.id ? (
            <TouchableOpacity onPress={() => setConfirmDeleteId(null)}>
              <Text style={[styles.actionText, { color: colors.textMuted }]}>Cancel</Text>
            </TouchableOpacity>
          ) : null}
        </View>
      </TouchableOpacity>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>Your history</Text>
        <Text style={styles.screenTitle}>Library</Text>
        <TouchableOpacity
          style={styles.newButton}
          onPress={() => router.push("/reflection/new")}
        >
          <Text style={styles.newButtonText}>+ New</Text>
        </TouchableOpacity>
      </View>

      {loading && reflections.length === 0 && (
        <View style={styles.stateCard}>
          <ActivityIndicator color={colors.text} />
          <Text style={styles.stateTitle}>Loading reflections</Text>
          <Text style={styles.stateText}>Pulling in your saved drafts and plans.</Text>
        </View>
      )}

      {!loading && error ? (
        <View style={styles.stateCard}>
          <Text style={styles.stateTitle}>Something did not connect</Text>
          <Text style={styles.stateText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={load}>
            <Text style={styles.retryText}>Try again</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {!loading && !error && reflections.length === 0 && (
        <View style={styles.stateCard}>
          <Text style={styles.emptyTitle}>No reflections yet</Text>
          <Text style={styles.emptyHint}>
            Start with one moment that feels unresolved. You can keep it as a draft or generate a plan when you are ready.
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => router.push("/reflection/new")}>
            <Text style={styles.retryText}>Start a reflection</Text>
          </TouchableOpacity>
        </View>
      )}

      {!error && reflections.length > 0 ? (
        <FlatList
          data={reflections}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          onRefresh={load}
          refreshing={loading}
        />
      ) : null}
    </SafeAreaView>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "#E8A87C",
    completed: "#7EB89E",
    archived: "#A0A0A0",
  };
  return (
    <View style={[styles.badge, { backgroundColor: colors[status] ?? "#A0A0A0" }]}>
      <Text style={styles.badgeText}>{status}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 16,
  },
  eyebrow: { fontSize: 12, fontWeight: "700", color: colors.textQuiet, textTransform: "uppercase", letterSpacing: 1, alignSelf: "flex-start" },
  screenTitle: { fontSize: 28, fontWeight: "700", color: colors.text, alignSelf: "flex-start" },
  newButton: {
    backgroundColor: colors.text,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: radii.pill,
    position: "absolute",
    right: 20,
    bottom: 18,
  },
  newButtonText: { color: "#FFF", fontSize: 14, fontWeight: "700" },
  stateCard: {
    margin: 20,
    marginTop: 46,
    padding: 22,
    alignItems: "center",
    backgroundColor: colors.surfaceSoft,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.04)",
    ...shadow.card,
  },
  stateTitle: { fontSize: 18, fontWeight: "700", color: colors.text, marginTop: 12, marginBottom: 8, textAlign: "center" },
  stateText: { fontSize: 14, color: colors.textMuted, lineHeight: 21, textAlign: "center" },
  emptyTitle: { fontSize: 18, fontWeight: "700", color: colors.text, marginBottom: 8 },
  emptyHint: { fontSize: 14, color: colors.textMuted, textAlign: "center", lineHeight: 21 },
  retryButton: { marginTop: 18, paddingHorizontal: 18, paddingVertical: 11, borderRadius: radii.pill, borderWidth: 1, borderColor: colors.border },
  retryText: { color: colors.text, fontSize: 14, fontWeight: "700" },
  list: { paddingHorizontal: 20, paddingBottom: 32 },
  card: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: radii.card,
    padding: 18,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.04)",
    ...shadow.card,
  },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  cardTitle: { fontSize: 17, fontWeight: "700", color: colors.text, flex: 1, marginRight: 8 },
  badge: { paddingHorizontal: 9, paddingVertical: 4, borderRadius: radii.pill },
  badgeText: { color: "#FFF", fontSize: 11, fontWeight: "600", textTransform: "capitalize" },
  cardSituation: { fontSize: 14, color: colors.textMuted, marginBottom: 8, lineHeight: 21 },
  cardDate: { fontSize: 12, color: colors.textQuiet, marginBottom: 12 },
  cardActions: { flexDirection: "row", gap: 16 },
  actionText: { fontSize: 13, color: colors.text, fontWeight: "700" },
});
