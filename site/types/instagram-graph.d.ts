/**
 * Instagram Graph API — TypeScript types
 * Generated: 2026-10-13
 * Base: https://graph.facebook.com/{version} (examples use v21.0)
 * Companion to openapi.yaml in this bundle. Verify against Meta docs before shipping.
 */

export interface GraphError {
  error: {
    message: string;
    type: string;
    code: number;
    error_subcode?: number;
    fbtrace_id?: string;
  };
}

export interface Paging {
  cursors?: { before?: string; after?: string };
  next?: string;
}

export interface IgUser {
  id: string;
  username: string;
  account_type: "BUSINESS" | "CREATOR" | "MEDIA_CREATOR";
  media_count: number;
}

export type MediaType = "IMAGE" | "VIDEO" | "CAROUSEL_ALBUM";
export type MediaProductType = "FEED" | "REELS" | "STORY";

export interface Media {
  id: string;
  caption?: string;
  media_type: MediaType;
  media_product_type?: MediaProductType;
  media_url?: string;
  thumbnail_url?: string;
  permalink?: string;
  timestamp?: string;
  like_count?: number;
  comments_count?: number;
}

export interface MediaList {
  data: Media[];
  paging?: Paging;
}

/** Step 1 of publishing: POST /{ig-user-id}/media */
export interface CreateContainerRequest {
  image_url?: string;
  video_url?: string;
  media_type?: "REELS" | "CAROUSEL" | "STORIES";
  caption?: string;
  location_id?: string;
  alt_text?: string;
  is_carousel_item?: boolean;
  children?: string; // comma-separated container IDs
  share_to_feed?: boolean;
}

export interface Container {
  id: string;
}

export type ContainerStatusCode = "IN_PROGRESS" | "FINISHED" | "ERROR" | "EXPIRED" | "PUBLISHED";

export interface ContainerStatus {
  id: string;
  status_code: ContainerStatusCode;
  status?: string;
}

/** Step 2 of publishing: POST /{ig-user-id}/media_publish */
export interface PublishRequest {
  creation_id: string;
}

export interface PublishedMedia {
  id: string;
}

export interface InsightValue {
  value: number | Record<string, number>;
  end_time?: string;
}

export interface Insight {
  name: string;
  period: string;
  values: InsightValue[];
  id?: string;
}

export interface InsightsResponse {
  data: Insight[];
}

export interface IgComment {
  id: string;
  text: string;
  username?: string;
  timestamp?: string;
  like_count?: number;
  hidden?: boolean;
}

export interface CommentList {
  data: IgComment[];
  paging?: Paging;
}

export interface SendMessageRequest {
  recipient: { id: string }; // IGSID
  message: { text?: string; attachment?: unknown };
  messaging_type?: "RESPONSE" | "UPDATE" | "MESSAGE_TAG";
  tag?: string;
}

export interface SendMessageResponse {
  recipient_id: string;
  message_id: string;
}

export interface WebhookChange {
  field: string;
  value: Record<string, unknown>;
}

export interface WebhookEntry {
  id: string;
  time: number;
  changes?: WebhookChange[];
  messaging?: Array<Record<string, unknown>>;
}

export interface WebhookPayload {
  object: string; // "instagram"
  entry: WebhookEntry[];
}

export interface Hashtag {
  id: string;
  name: string;
}

export interface PublishingLimit {
  data: Array<{
    quota_usage: number;
    rate_limit_settings?: Array<Record<string, number>>;
    config?: { quota_total?: number; quota_duration?: number };
  }>;
}

export interface Conversation {
  id: string;
  participants?: unknown;
  updated_time?: string;
}

export interface ConversationList {
  data: Conversation[];
  paging?: Paging;
}

export interface UpdateMediaRequest {
  caption?: string;
  comment_enabled?: boolean;
}

export interface SuccessResponse {
  success: boolean;
}

/** Minimal typed client signature used by examples/ */
export interface GraphClient {
  get<T>(path: string, params?: Record<string, string>): Promise<T>;
  post<T>(path: string, body: Record<string, string>): Promise<T>;
}
