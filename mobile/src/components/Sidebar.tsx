import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  useColorScheme,
  TouchableOpacity,
  Platform,
  ScrollView,
  Dimensions,
} from 'react-native';
import { 
  Text, 
  Switch, 
  Button, 
  Menu, 
  Divider, 
  TextInput, 
  Modal, 
  Portal, 
  IconButton,
  Badge,
  Surface
} from 'react-native-paper';
import { BlurView } from 'expo-blur';
import { getTheme } from '../utils/theme';
import * as Haptics from 'expo-haptics';

/**
 * User profiles with avatars and display names
 */
const USER_PROFILES = {
  default: { name: 'Default User', avatar: '👤', status: 'online' },
  user1: { name: 'Alice', avatar: '👩‍💼', status: 'online' },
  user2: { name: 'Bob', avatar: '👨‍💻', status: 'away' },
  user3: { name: 'Charlie', avatar: '🧑‍🔬', status: 'offline' },
};

interface SidebarProps {
  visible: boolean;
  onClose: () => void;
  userId: string;
  onUserChange: (userId: string) => void;
  isTestMode: boolean;
  onTestModeChange: (value: boolean) => void;
  themeMode: 'system' | 'light' | 'dark';
  onThemeModeChange: (mode: 'system' | 'light' | 'dark') => void;
  effectiveScheme?: 'light' | 'dark' | null;
}

const Sidebar: React.FC<SidebarProps> = ({
  visible,
  onClose,
  userId,
  onUserChange,
  isTestMode,
  onTestModeChange,
  themeMode,
  onThemeModeChange,
  effectiveScheme,
}) => {
  const [customUserDialogVisible, setCustomUserDialogVisible] = useState(false);
  const [customUserId, setCustomUserId] = useState('');
  const scheme = effectiveScheme || useColorScheme();
  const theme = getTheme(scheme);
  const { width: screenWidth } = Dimensions.get('window');
  const sidebarWidth = Math.min(320, screenWidth * 0.85);

  const getUserProfile = (id: string) => {
    return USER_PROFILES[id as keyof typeof USER_PROFILES] || { 
      name: id, 
      avatar: '👤', 
      status: 'online' 
    };
  };

  const handleUserSelect = async (newUserId: string) => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onUserChange(newUserId);
    // Don't close sidebar here - let the parent handle it
  };

  const handleCustomUserSubmit = () => {
    if (customUserId.trim()) {
      onUserChange(customUserId.trim());
      setCustomUserId('');
      setCustomUserDialogVisible(false);
      // Sidebar will close via onUserChange callback in parent
    }
  };

  const handleTestModeToggle = async (value: boolean) => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onTestModeChange(value);
    // Keep sidebar open for test mode toggle
  };

  const handleThemeModeChange = async (mode: 'system' | 'light' | 'dark') => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onThemeModeChange(mode);
  };

  if (!visible) return null;

  return (
    <>
      <Portal>
        <View style={styles.container}>
          {/* Blur Backdrop */}
          <TouchableOpacity 
            style={styles.backdrop} 
            activeOpacity={1} 
            onPress={onClose}
          >
            {Platform.OS === 'web' ? (
              <BlurView 
                style={StyleSheet.absoluteFill} 
                intensity={20} 
                tint={scheme === 'dark' ? 'dark' : 'light'}
              />
            ) : (
              <BlurView 
                style={StyleSheet.absoluteFill} 
                intensity={15} 
                tint={scheme === 'dark' ? 'dark' : 'light'}
              />
            )}
          </TouchableOpacity>

          {/* Sidebar */}
          <View 
            style={[
              styles.sidebar, 
              { 
                backgroundColor: theme.background,
                width: sidebarWidth,
                borderRightColor: theme.border + '30',
              }
            ]}
          >
            {/* Header */}
            <View style={[styles.header, { borderBottomColor: theme.border + '20' }]}>
              <View style={styles.headerContent}>
                <Text style={[styles.headerTitle, { color: theme.text }]}>
                  Settings
                </Text>
                <IconButton 
                  icon="close" 
                  size={24} 
                  onPress={onClose}
                  iconColor={theme.textSecondary}
                />
              </View>
            </View>

            <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
              {/* Current User Section */}
              <View style={[styles.section, { borderBottomColor: theme.border + '15' }]}>
                <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
                  CURRENT USER
                </Text>
                <View 
                  style={[styles.currentUserCard, { backgroundColor: theme.backgroundSecondary }]}
                >
                  <View style={styles.currentUserInfo}>
                    <Text style={[styles.userAvatar, { color: theme.text }]}>
                      {getUserProfile(userId).avatar}
                    </Text>
                    <View style={styles.userDetails}>
                      <Text style={[styles.userName, { color: theme.text }]}>
                        {getUserProfile(userId).name}
                      </Text>
                      <View style={styles.userMeta}>
                        <View 
                          style={[
                            styles.statusBadge, 
                            { backgroundColor: getUserProfile(userId).status === 'online' ? '#4CAF50' : getUserProfile(userId).status === 'away' ? '#FF9800' : '#9E9E9E' }
                          ]}
                        />
                        <Text style={[styles.userStatus, { color: theme.textSecondary }]}>
                          {getUserProfile(userId).status}
                        </Text>
                        <Text style={[styles.userIdText, { color: theme.textSecondary }]}>
                          • {userId}
                        </Text>
                      </View>
                    </View>
                  </View>
                </View>
              </View>

              {/* User Selection */}
              <View style={[styles.section, { borderBottomColor: theme.border + '15' }]}>
                <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
                  SWITCH USER
                </Text>
                {Object.entries(USER_PROFILES).map(([id, profile]) => (
                  <TouchableOpacity
                    key={id}
                    style={[
                      styles.userOption,
                      userId === id && { backgroundColor: theme.primary + '10' },
                      { borderColor: theme.border + '15' }
                    ]}
                    onPress={() => handleUserSelect(id)}
                    activeOpacity={0.6}
                  >
                    <Text style={[styles.optionAvatar, { color: theme.text }]}>
                      {profile.avatar}
                    </Text>
                    <View style={styles.optionContent}>
                      <Text style={[
                        styles.optionName, 
                        { color: userId === id ? theme.primary : theme.text }
                      ]}>
                        {profile.name}
                      </Text>
                      <View style={styles.optionMeta}>
                        <View 
                          style={[
                            styles.statusBadge, 
                            { backgroundColor: profile.status === 'online' ? '#4CAF50' : profile.status === 'away' ? '#FF9800' : '#9E9E9E' }
                          ]}
                        />
                        <Text style={[styles.optionStatus, { color: theme.textSecondary }]}>
                          {profile.status}
                        </Text>
                      </View>
                    </View>
                    {userId === id && (
                      <IconButton 
                        icon="check" 
                        size={20} 
                        iconColor={theme.primary}
                      />
                    )}
                  </TouchableOpacity>
                ))}
                
                <TouchableOpacity
                  style={[styles.customUserOption, { borderColor: theme.border + '15' }]}
                  onPress={() => setCustomUserDialogVisible(true)}
                  activeOpacity={0.6}
                >
                  <IconButton 
                    icon="account-plus" 
                    size={20} 
                    iconColor={theme.primary}
                  />
                  <Text style={[styles.customUserText, { color: theme.primary }]}>
                    Add Custom User
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Settings Section */}
              <View style={[styles.section, { borderBottomColor: theme.border + '15' }]}>
                <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
                  SETTINGS
                </Text>
                
                {/* Test Mode Toggle */}
                <View style={[styles.settingRow, { backgroundColor: theme.backgroundSecondary }]}>
                  <View style={styles.settingInfo}>
                    <Text style={[styles.settingTitle, { color: theme.text }]}>
                      Test Mode
                    </Text>
                    <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                      Use test API endpoint for development
                    </Text>
                  </View>
                  <Switch
                    value={isTestMode}
                    onValueChange={handleTestModeToggle}
                    thumbColor={isTestMode ? theme.primary : theme.textSecondary}
                    trackColor={{ 
                      false: theme.textSecondary + '30', 
                      true: theme.primary + '30' 
                    }}
                  />
                </View>

                {/* Theme Mode Toggle */}
                <View style={[styles.settingRow, { backgroundColor: theme.backgroundSecondary }]}>
                  <View style={styles.settingInfo}>
                    <Text style={[styles.settingTitle, { color: theme.text }]}>
                      Theme Mode
                    </Text>
                    <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                      Choose between System, Light, and Dark themes
                    </Text>
                  </View>
                </View>
                
                {/* Theme Selection Buttons */}
                <View style={[styles.themeSelector, { backgroundColor: theme.backgroundSecondary }]}>
                  {(['system', 'light', 'dark'] as const).map((mode) => (
                    <TouchableOpacity
                      key={mode}
                      style={[
                        styles.themeOption,
                        themeMode === mode && [styles.themeOptionActive, { backgroundColor: theme.primary }],
                      ]}
                      onPress={() => handleThemeModeChange(mode)}
                      activeOpacity={0.6}
                    >
                      <Text style={[
                        styles.themeOptionText,
                        { color: themeMode === mode ? '#fff' : theme.text }
                      ]}>
                        {mode.charAt(0).toUpperCase() + mode.slice(1)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {/* App Info Section */}
              <View style={styles.section}>
                <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
                  APP INFO
                </Text>
                
                <View style={[styles.infoRow, { backgroundColor: theme.backgroundSecondary }]}>
                  <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>
                    Version
                  </Text>
                  <Text style={[styles.infoValue, { color: theme.text }]}>
                    1.0.0 (Build 42)
                  </Text>
                </View>
                
                <View style={[styles.infoRow, { backgroundColor: theme.backgroundSecondary }]}>
                  <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>
                    Platform
                  </Text>
                  <Text style={[styles.infoValue, { color: theme.text }]}>
                    {Platform.OS === 'ios' ? 'iOS' : Platform.OS === 'android' ? 'Android' : 'Web'}
                  </Text>
                </View>
                
                <View style={[styles.infoRow, { backgroundColor: theme.backgroundSecondary }]}>
                  <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>
                    Theme
                  </Text>
                  <Text style={[styles.infoValue, { color: theme.text }]}>
                    {themeMode === 'system' ? `System (${scheme === 'dark' ? 'Dark' : 'Light'})` : themeMode === 'dark' ? 'Dark' : 'Light'}
                  </Text>
                </View>
              </View>
            </ScrollView>

            {/* Footer */}
            <View style={[styles.footer, { borderTopColor: theme.border + '20' }]}>
              <Text style={[styles.footerText, { color: theme.textSecondary }]}>
                © {new Date().getFullYear()} Ted AI
              </Text>
            </View>
          </View>
        </View>
      </Portal>

      {/* Custom User Dialog - Separate Portal to avoid blur effect */}
      <Portal>
        <Modal
          visible={customUserDialogVisible}
          onDismiss={() => setCustomUserDialogVisible(false)}
          contentContainerStyle={[styles.modalContent, { backgroundColor: theme.background }]}
        >
          <Text style={[styles.modalTitle, { color: theme.text }]}>
            Add Custom User
          </Text>
          <Text style={[styles.modalDescription, { color: theme.textSecondary }]}>
            Enter a unique identifier for the new user
          </Text>
          <TextInput
            value={customUserId}
            onChangeText={setCustomUserId}
            mode="outlined"
            style={styles.modalInput}
            autoFocus
            returnKeyType="done"
            onSubmitEditing={handleCustomUserSubmit}
            placeholder="Enter user ID"
            right={<TextInput.Icon icon="account-check" />}
          />
          <View style={styles.modalButtons}>
            <Button onPress={() => setCustomUserDialogVisible(false)}>
              Cancel
            </Button>
            <Button 
              onPress={handleCustomUserSubmit} 
              mode="contained" 
              disabled={!customUserId.trim()}
            >
              Add User
            </Button>
          </View>
        </Modal>
      </Portal>
    </>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1000,
  },
  backdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1001,
  },
  sidebar: {
    position: 'absolute',
    top: 0,
    left: 0,
    bottom: 0,
    zIndex: 1002,
    borderTopRightRadius: 0,
    borderBottomRightRadius: 0,
    borderRightWidth: StyleSheet.hairlineWidth,
    shadowColor: '#000',
    shadowOffset: { width: 2, height: 0 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 5,
  },
  header: {
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    letterSpacing: -0.5,
  },
  content: {
    flex: 1,
  },
  section: {
    paddingVertical: 20,
    paddingHorizontal: 20,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  currentUserCard: {
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  currentUserInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  userAvatar: {
    fontSize: 32,
    marginRight: 12,
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  userMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusBadge: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  userStatus: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  userIdText: {
    fontSize: 12,
    marginLeft: 4,
  },
  userOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  optionAvatar: {
    fontSize: 20,
    marginRight: 12,
  },
  optionContent: {
    flex: 1,
  },
  optionName: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  optionMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionStatus: {
    fontSize: 11,
    textTransform: 'capitalize',
  },
  customUserOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginTop: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderStyle: 'dashed',
  },
  customUserText: {
    fontSize: 16,
    fontWeight: '500',
    marginLeft: 8,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
  },
  settingInfo: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  settingDescription: {
    fontSize: 12,
    lineHeight: 16,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 8,
  },
  infoLabel: {
    fontSize: 14,
    fontWeight: '500',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '400',
  },
  footer: {
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderTopWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 11,
    fontWeight: '500',
  },
  modalContent: {
    padding: 24,
    margin: 20,
    borderRadius: 16,
    zIndex: 2000,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 8,
  },
  modalDescription: {
    fontSize: 14,
    marginBottom: 20,
    lineHeight: 20,
  },
  modalInput: {
    marginBottom: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  themeSelector: {
    flexDirection: 'row',
    borderRadius: 8,
    padding: 4,
    marginTop: 8,
    marginHorizontal: 16,
  },
  themeOption: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  themeOptionActive: {
    // backgroundColor will be set dynamically
  },
  themeOptionText: {
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
  },
});

export default Sidebar; 