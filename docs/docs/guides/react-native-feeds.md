---
sidebar_position: 5
title: React Native Feeds
description: Complete feed system and user discovery for React Native apps
---

# React Native Feeds

Complete guide for integrating user discovery, feed browsing, and real-time updates into React Native applications.

## Overview

- **User Discovery**: Find and browse available listeners
- **Feed Filtering**: Filter listeners by various criteria
- **Feed Statistics**: Get insights about the feed system
- **Real-time Updates**: WebSocket support for live feed updates

## Feed Service

### Feed Service Implementation

```typescript
// services/FeedService.ts
import ApiService from './ApiService';

export interface Listener {
  user_id: number;
  username: string;
  sex: 'male' | 'female';
  bio: string;
  interests: string[];
  profile_image_url?: string;
  preferred_language?: string;
  rating: number;
  country: string;
  roles: string[];
  is_online: boolean;
  is_busy: boolean;
  last_seen: string;
  wait_time?: number;
  is_available: boolean;
}

export interface FeedResponse {
  listeners: Listener[];
  total_count: number;
  online_count: number;
  available_count: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface FeedFilters {
  online_only?: boolean;
  available_only?: boolean;
  language?: string;
  interests?: string;
  min_rating?: number;
  page?: number;
  per_page?: number;
}

export interface FeedStats {
  total_listeners: number;
  online_listeners: number;
  busy_listeners: number;
  available_listeners: number;
  average_rating: number;
  top_interests: InterestCount[];
  gender_distribution: GenderDistribution;
  language_distribution: LanguageDistribution;
  last_updated: string;
}

export interface InterestCount {
  interest: string;
  count: number;
}

export interface GenderDistribution {
  female: number;
  male: number;
  other: number;
}

export interface LanguageDistribution {
  [key: string]: number;
}

class FeedService {
  // Get listeners feed
  async getListenersFeed(filters: Partial<FeedFilters> = {}): Promise<FeedResponse> {
    const params = new URLSearchParams();
    
    if (filters.online_only !== undefined) params.append('online_only', filters.online_only.toString());
    if (filters.available_only !== undefined) params.append('available_only', filters.available_only.toString());
    if (filters.language) params.append('language', filters.language);
    if (filters.interests) params.append('interests', filters.interests);
    if (filters.min_rating !== undefined) params.append('min_rating', filters.min_rating.toString());
    if (filters.page !== undefined) params.append('page', filters.page.toString());
    if (filters.per_page !== undefined) params.append('per_page', filters.per_page.toString());

    return ApiService.get<FeedResponse>(`/feed/listeners?${params}`);
  }

  // Get feed statistics
  async getFeedStats(): Promise<FeedStats> {
    return ApiService.get<FeedStats>('/feed/stats');
  }
}

export default new FeedService();
```

## Feed Screens

### Feed List Screen

```typescript
// screens/FeedListScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  TextInput,
} from 'react-native';
import FeedService, { Listener, FeedFilters } from '../services/FeedService';
import ListenerCard from '../components/ListenerCard';
import FilterModal from '../components/FilterModal';

const FeedListScreen: React.FC = () => {
  const [listeners, setListeners] = useState<Listener[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(true);
  const [filters, setFilters] = useState<FeedFilters>({
    online_only: false,
    min_rating: 0,
    max_rating: 5,
    interests: [],
    sort_by: 'rating',
    sort_order: 'desc',
  });
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadListeners(true);
  }, [filters]);

  const loadListeners = async (reset: boolean = false) => {
    if (reset) {
      setPage(1);
      setIsLoading(true);
    } else {
      setLoadingMore(true);
    }

    try {
      const currentPage = reset ? 1 : page;
      const response = await FeedService.getListenersFeed(filters, currentPage, 20);
      
      if (reset) {
        setListeners(response.listeners);
      } else {
        setListeners(prev => [...prev, ...response.listeners]);
      }
      
      setHasNext(response.pagination.has_next);
      setPage(currentPage + 1);
    } catch (error) {
      console.error('Failed to load listeners:', error);
    } finally {
      setIsLoading(false);
      setLoadingMore(false);
    }
  };

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    loadListeners(true).finally(() => setRefreshing(false));
  }, [filters]);

  const handleLoadMore = () => {
    if (!loadingMore && hasNext) {
      loadListeners(false);
    }
  };

  const handleFilterChange = (newFilters: FeedFilters) => {
    setFilters(newFilters);
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    // Implement search logic here
  };

  const filteredListeners = listeners.filter(listener =>
    searchQuery === '' ||
    listener.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    listener.bio.toLowerCase().includes(searchQuery.toLowerCase()) ||
    listener.interests.some(interest =>
      interest.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  const renderListener = ({ item }: { item: Listener }) => (
    <ListenerCard
      listener={item}
      onPress={() => {
        // Navigate to listener profile or start call
      }}
    />
  );

  const renderFooter = () => {
    if (!loadingMore) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color="#007AFF" />
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search listeners..."
          value={searchQuery}
          onChangeText={handleSearch}
        />
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => setShowFilters(true)}
        >
          <Text style={styles.filterButtonText}>Filters</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={filteredListeners}
        renderItem={renderListener}
        keyExtractor={(item) => item.user_id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={renderFooter}
        contentContainerStyle={styles.listContainer}
      />

      <FilterModal
        visible={showFilters}
        filters={filters}
        onClose={() => setShowFilters(false)}
        onApply={handleFilterChange}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    padding: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  searchInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
  },
  filterButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
  },
  filterButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  listContainer: {
    padding: 10,
  },
  footerLoader: {
    padding: 20,
    alignItems: 'center',
  },
});

export default FeedListScreen;
```

### Listener Card Component

```typescript
// components/ListenerCard.tsx
import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
} from 'react-native';
import { Listener } from '../services/FeedService';
import StatusIndicator from './StatusIndicator';

interface ListenerCardProps {
  listener: Listener;
  onPress: () => void;
}

const ListenerCard: React.FC<ListenerCardProps> = ({ listener, onPress }) => {
  const formatLastSeen = (lastSeen: string) => {
    const date = new Date(lastSeen);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  return (
    <TouchableOpacity style={styles.card} onPress={onPress}>
      <View style={styles.header}>
        <View style={styles.profileContainer}>
          {listener.profile_image_url ? (
            <Image
              source={{ uri: listener.profile_image_url }}
              style={styles.profileImage}
            />
          ) : (
            <View style={styles.placeholderImage}>
              <Text style={styles.placeholderText}>
                {listener.username.charAt(0).toUpperCase()}
              </Text>
            </View>
          )}
          
          <View style={styles.profileInfo}>
            <Text style={styles.username}>{listener.username}</Text>
            <StatusIndicator
              isOnline={listener.is_online}
              isBusy={listener.is_busy}
              size="small"
            />
          </View>
        </View>
        
        <View style={styles.ratingContainer}>
          <Text style={styles.rating}>⭐ {listener.rating.toFixed(1)}</Text>
        </View>
      </View>

      <Text style={styles.bio} numberOfLines={2}>
        {listener.bio}
      </Text>

      <View style={styles.interestsContainer}>
        {listener.interests.slice(0, 3).map((interest, index) => (
          <View key={index} style={styles.interestTag}>
            <Text style={styles.interestText}>{interest}</Text>
          </View>
        ))}
        {listener.interests.length > 3 && (
          <Text style={styles.moreInterests}>
            +{listener.interests.length - 3} more
          </Text>
        )}
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Calls</Text>
          <Text style={styles.statValue}>{listener.call_count}</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Avg Duration</Text>
          <Text style={styles.statValue}>{listener.avg_call_duration.toFixed(1)}m</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Last Seen</Text>
          <Text style={styles.statValue}>{formatLastSeen(listener.last_seen)}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    marginBottom: 10,
    padding: 15,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  profileContainer: {
    flexDirection: 'row',
    flex: 1,
  },
  profileImage: {
    width: 50,
    height: 50,
    borderRadius: 25,
    marginRight: 10,
  },
  placeholderImage: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  placeholderText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  profileInfo: {
    flex: 1,
  },
  username: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  ratingContainer: {
    alignItems: 'flex-end',
  },
  rating: {
    fontSize: 14,
    color: '#FFD700',
    fontWeight: 'bold',
  },
  bio: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
    lineHeight: 18,
  },
  interestsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 10,
  },
  interestTag: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 6,
    marginBottom: 4,
  },
  interestText: {
    fontSize: 12,
    color: '#007AFF',
  },
  moreInterests: {
    fontSize: 12,
    color: '#666',
    alignSelf: 'center',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 10,
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  statValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
});

export default ListenerCard;
```

### Filter Modal Component

```typescript
// components/FilterModal.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Picker,
  Switch,
} from 'react-native';
import { FeedFilters } from '../services/FeedService';

interface FilterModalProps {
  visible: boolean;
  filters: FeedFilters;
  onClose: () => void;
  onApply: (filters: FeedFilters) => void;
}

const FilterModal: React.FC<FilterModalProps> = ({
  visible,
  filters,
  onClose,
  onApply,
}) => {
  const [localFilters, setLocalFilters] = useState<FeedFilters>(filters);

  const handleApply = () => {
    onApply(localFilters);
    onClose();
  };

  const handleReset = () => {
    setLocalFilters({
      online_only: false,
      min_rating: 0,
      max_rating: 5,
      interests: [],
      sort_by: 'rating',
      sort_order: 'desc',
    });
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose}>
            <Text style={styles.cancelButton}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Filters</Text>
          <TouchableOpacity onPress={handleApply}>
            <Text style={styles.applyButton}>Apply</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content}>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Status</Text>
            <View style={styles.switchContainer}>
              <Text style={styles.switchLabel}>Online Only</Text>
              <Switch
                value={localFilters.online_only}
                onValueChange={(value) =>
                  setLocalFilters({ ...localFilters, online_only: value })
                }
              />
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Gender</Text>
            <Picker
              selectedValue={localFilters.sex || ''}
              onValueChange={(value) =>
                setLocalFilters({ ...localFilters, sex: value || undefined })
              }
              style={styles.picker}
            >
              <Picker.Item label="All" value="" />
              <Picker.Item label="Male" value="male" />
              <Picker.Item label="Female" value="female" />
              <Picker.Item label="Other" value="other" />
            </Picker>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Rating Range</Text>
            <View style={styles.ratingContainer}>
              <Text style={styles.ratingLabel}>Min: {localFilters.min_rating}</Text>
              <Picker
                selectedValue={localFilters.min_rating}
                onValueChange={(value) =>
                  setLocalFilters({ ...localFilters, min_rating: value })
                }
                style={styles.ratingPicker}
              >
                {[0, 1, 2, 3, 4, 5].map((rating) => (
                  <Picker.Item key={rating} label={rating.toString()} value={rating} />
                ))}
              </Picker>
            </View>
            <View style={styles.ratingContainer}>
              <Text style={styles.ratingLabel}>Max: {localFilters.max_rating}</Text>
              <Picker
                selectedValue={localFilters.max_rating}
                onValueChange={(value) =>
                  setLocalFilters({ ...localFilters, max_rating: value })
                }
                style={styles.ratingPicker}
              >
                {[0, 1, 2, 3, 4, 5].map((rating) => (
                  <Picker.Item key={rating} label={rating.toString()} value={rating} />
                ))}
              </Picker>
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Sort By</Text>
            <Picker
              selectedValue={localFilters.sort_by}
              onValueChange={(value) =>
                setLocalFilters({ ...localFilters, sort_by: value })
              }
              style={styles.picker}
            >
              <Picker.Item label="Rating" value="rating" />
              <Picker.Item label="Online Status" value="online" />
              <Picker.Item label="Recent" value="recent" />
            </Picker>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Sort Order</Text>
            <Picker
              selectedValue={localFilters.sort_order}
              onValueChange={(value) =>
                setLocalFilters({ ...localFilters, sort_order: value })
              }
              style={styles.picker}
            >
              <Picker.Item label="Descending" value="desc" />
              <Picker.Item label="Ascending" value="asc" />
            </Picker>
          </View>
        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity style={styles.resetButton} onPress={handleReset}>
            <Text style={styles.resetButtonText}>Reset</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  cancelButton: {
    fontSize: 16,
    color: '#007AFF',
  },
  applyButton: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    padding: 15,
  },
  section: {
    backgroundColor: '#fff',
    marginBottom: 15,
    padding: 15,
    borderRadius: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  switchLabel: {
    fontSize: 16,
    color: '#333',
  },
  picker: {
    backgroundColor: '#f9f9f9',
  },
  ratingContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  ratingLabel: {
    fontSize: 14,
    color: '#666',
  },
  ratingPicker: {
    width: 80,
    backgroundColor: '#f9f9f9',
  },
  footer: {
    padding: 15,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  resetButton: {
    backgroundColor: '#FF3B30',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  resetButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default FilterModal;
```

### Feed Statistics Screen

```typescript
// screens/FeedStatsScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import FeedService, { FeedStats } from '../services/FeedService';

const FeedStatsScreen: React.FC = () => {
  const [stats, setStats] = useState<FeedStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const feedStats = await FeedService.getFeedStats();
      setStats(feedStats);
    } catch (error) {
      console.error('Failed to load feed stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadStats();
    setRefreshing(false);
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (!stats) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Failed to load statistics</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }
    >
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Overview</Text>
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.total_listeners}</Text>
            <Text style={styles.statLabel}>Total Listeners</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.online_listeners}</Text>
            <Text style={styles.statLabel}>Online</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.available_listeners}</Text>
            <Text style={styles.statLabel}>Available</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.average_rating.toFixed(1)}</Text>
            <Text style={styles.statLabel}>Avg Rating</Text>
          </View>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Top Interests</Text>
        {stats.top_interests.map((interest, index) => (
          <View key={index} style={styles.interestItem}>
            <Text style={styles.interestName}>{interest.interest}</Text>
            <Text style={styles.interestCount}>{interest.count} listeners</Text>
          </View>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Gender Distribution</Text>
        <View style={styles.distributionContainer}>
          <View style={styles.distributionItem}>
            <Text style={styles.distributionLabel}>Female</Text>
            <Text style={styles.distributionValue}>{stats.gender_distribution.female}</Text>
          </View>
          <View style={styles.distributionItem}>
            <Text style={styles.distributionLabel}>Male</Text>
            <Text style={styles.distributionValue}>{stats.gender_distribution.male}</Text>
          </View>
          <View style={styles.distributionItem}>
            <Text style={styles.distributionLabel}>Other</Text>
            <Text style={styles.distributionValue}>{stats.gender_distribution.other}</Text>
          </View>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Language Distribution</Text>
        {Object.entries(stats.language_distribution).map(([language, count]) => (
          <View key={language} style={styles.languageItem}>
            <Text style={styles.languageName}>{language.toUpperCase()}</Text>
            <Text style={styles.languageCount}>{count} listeners</Text>
          </View>
        ))}
      </View>

      <Text style={styles.lastUpdated}>
        Last updated: {new Date(stats.last_updated).toLocaleString()}
      </Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#FF3B30',
  },
  section: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 15,
    borderRadius: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 5,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  interestItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  interestName: {
    fontSize: 16,
    color: '#333',
    textTransform: 'capitalize',
  },
  interestCount: {
    fontSize: 14,
    color: '#666',
  },
  distributionContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  distributionItem: {
    alignItems: 'center',
  },
  distributionLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  distributionValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  languageItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  languageName: {
    fontSize: 16,
    color: '#333',
    fontWeight: 'bold',
  },
  languageCount: {
    fontSize: 14,
    color: '#666',
  },
  lastUpdated: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    margin: 20,
  },
});

export default FeedStatsScreen;
```

## Best Practices

### Feed Management

1. **Pagination**: Always use pagination for large feeds
2. **Filtering**: Use appropriate filters to reduce data load
3. **Caching**: Cache feed data locally for better performance
4. **Real-time Updates**: Use WebSocket for live updates

### User Experience

1. **Loading States**: Show loading indicators during data fetch
2. **Empty States**: Handle empty feeds gracefully
3. **Search Functionality**: Implement efficient search
4. **Filter UI**: Provide intuitive filter controls

### Performance

1. **Lazy Loading**: Load more items as needed
2. **Image Optimization**: Optimize profile images
3. **Data Caching**: Cache frequently accessed data
4. **Efficient Filtering**: Use server-side filtering

## Next Steps

- Learn about [React Native Favorites](./react-native-favorites)
- Explore [React Native Blocking](./react-native-blocking)
- Check out [React Native WebSocket](./react-native-websocket)
