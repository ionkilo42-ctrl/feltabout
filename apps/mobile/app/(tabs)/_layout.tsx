import { Tabs } from "expo-router";
import React from "react";
import { Text } from "react-native";
import { colors } from "../../src/styles/theme";

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarStyle: {
          backgroundColor: colors.background,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          height: 64,
          paddingTop: 8,
        },
        tabBarActiveTintColor: colors.text,
        tabBarInactiveTintColor: colors.textQuiet,
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "500",
        },
        headerStyle: { backgroundColor: colors.background },
        headerTintColor: colors.text,
        headerTitleStyle: { fontWeight: "600" },
        headerShadowVisible: false,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color }) => (
            <TabIcon name="home" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="reflections"
        options={{
          title: "Library",
          tabBarIcon: ({ color }) => (
            <TabIcon name="reflections" color={color} />
          ),
        }}
      />
    </Tabs>
  );
}

function TabIcon({ name, color }: { name: string; color: string }) {
  // Simple text-based icons for MVP
  const icons: Record<string, string> = {
    home: "○",
    reflections: "◉",
  };
  return (
    <Text style={{ color, fontSize: 18 }}>{icons[name] ?? "○"}</Text>
  );
}
