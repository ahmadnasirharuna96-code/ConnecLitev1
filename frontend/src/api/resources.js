import apiClient from "./client";

export const ProfileAPI = {
  getMine: () => apiClient.get("/profile/").then((r) => r.data),
  update: (data) => apiClient.patch("/profile/", data).then((r) => r.data),
  getPublic: (userId) => apiClient.get(`/profile/${userId}/`).then((r) => r.data),
  listInterests: () => apiClient.get("/interests/").then((r) => r.data),
};

export const MatchingAPI = {
  discover: () => apiClient.get("/discover/").then((r) => r.data),
  matches: () => apiClient.get("/matches/").then((r) => r.data),
  sendRequest: (to_user_id) => apiClient.post("/matches/request/", { to_user_id }).then((r) => r.data),
  connections: (direction) =>
    apiClient.get("/connections/", { params: direction ? { direction } : {} }).then((r) => r.data),
  respond: (id, action) => apiClient.post(`/connections/${id}/respond/`, { action }).then((r) => r.data),
};

export const CommunitiesAPI = {
  list: () => apiClient.get("/communities/").then((r) => r.data),
  detail: (id) => apiClient.get(`/communities/${id}/`).then((r) => r.data),
  create: (data) => apiClient.post("/communities/", data).then((r) => r.data),
  join: (id) => apiClient.post(`/communities/${id}/join/`).then((r) => r.data),
  leave: (id) => apiClient.post(`/communities/${id}/leave/`).then((r) => r.data),
  members: (id) => apiClient.get(`/communities/${id}/members/`).then((r) => r.data),
};

export const MessagingAPI = {
  conversations: () => apiClient.get("/conversations/").then((r) => r.data),
  messages: (conversationId) => apiClient.get(`/conversations/${conversationId}/messages/`).then((r) => r.data),
  send: (to_user_id, content) => apiClient.post("/messages/", { to_user_id, content }).then((r) => r.data),
};

export const AirtimeAPI = {
  gift: (recipient_phone, amount) => apiClient.post("/airtime/gift/", { recipient_phone, amount }).then((r) => r.data),
  transactions: () => apiClient.get("/airtime/transactions/").then((r) => r.data),
};

export const NotificationsAPI = {
  list: () => apiClient.get("/notifications/").then((r) => r.data),
};

export const VoiceAPI = {
  startVerification: () => apiClient.post("/voice/verification/start/").then((r) => r.data),
};
