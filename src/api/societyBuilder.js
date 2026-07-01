import { get, post, put, del, api } from "./api";

export const getSimbaMainHub = () => get("/society-builder/main-hub");
export const getMySocieties = () => get("/society-builder/my-societies");
export const createSociety = (payload) => post("/society-builder/societies", payload);
export const getSociety = (id) => get(`/society-builder/societies/${id}`);
export const updateSociety = (id, payload) => api(`/society-builder/societies/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
export const applyForChapter = (id) => post(`/society-builder/societies/${id}/apply-chapter`, {});
export const saveBlueprintAudit = (id, payload) => post(`/society-builder/societies/${id}/blueprint-audit`, payload);
export const getLatestBlueprintAudit = (id) => get(`/society-builder/societies/${id}/blueprint-audit/latest`);
export const addFirstTenMember = (id, payload) => post(`/society-builder/societies/${id}/first-ten`, payload);
export const updateFirstTenMember = (id, memberId, payload) => api(`/society-builder/societies/${id}/first-ten/${memberId}`, { method: "PATCH", body: JSON.stringify(payload) });
export const deleteFirstTenMember = (id, memberId) => del(`/society-builder/societies/${id}/first-ten/${memberId}`);
export const savePurpose = (id, payload) => post(`/society-builder/societies/${id}/purpose`, payload);
export const saveCovenant = (id, payload) => post(`/society-builder/societies/${id}/covenant`, payload);
export const advanceSocietyStage = (id, target_stage) => post(`/society-builder/societies/${id}/advance-stage`, { target_stage });
export const getSocietyMemberHome = (id) => get(`/society-builder/societies/${id}/member-home`);
export const getMyInstitutionalProfile = (id) => get(`/society-builder/societies/${id}/institutional-profile/me`);
export const saveMyInstitutionalProfile = (id, payload) => post(`/society-builder/societies/${id}/institutional-profile/me`, payload);
export const updateMyInstitutionalProfile = (id, payload) => api(`/society-builder/societies/${id}/institutional-profile/me`, { method: "PATCH", body: JSON.stringify(payload) });
export const getSocietyDirectory = (id) => get(`/society-builder/societies/${id}/directory`);
export const getChapterApplications = () => get("/society-builder/admin/chapter-applications");
export const approveChapter = (id) => post(`/society-builder/admin/chapter-applications/${id}/approve`, {});
export const requestChapterChanges = (id) => post(`/society-builder/admin/chapter-applications/${id}/request-changes`, {});
export const declineChapter = (id) => post(`/society-builder/admin/chapter-applications/${id}/decline`, {});
export const activateFirst100DaysContainer = (id) => post(`/society-builder/societies/${id}/containers/first-100-days/activate`, {});
export const getActiveContainer = (id) => get(`/society-builder/societies/${id}/containers/active`);
export const getTrustBoard = (id) => get(`/society-builder/societies/${id}/trust-board`);
export const createTrustTask = (id, payload) => post(`/society-builder/societies/${id}/trust-board/tasks`, payload);
export const updateTrustTask = (id, taskId, payload) => api(`/society-builder/societies/${id}/trust-board/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify(payload) });

export const getTrustTaskReaderReference = (id, taskId) => get(`/society-builder/societies/${id}/trust-board/tasks/${taskId}/reader-reference`);

export const getSocietyIntelligence = (id, debug = false) => get(`/society-builder/societies/${id}/intelligence${debug ? "?debug=true" : ""}`);

export const getInstitutionIntelligence = (id, debug = false) => get(`/society-builder/institutions/${id}/intelligence${debug ? "?debug=true" : ""}`);

export const getOpportunityIntelligence = (id, debug = false) => get(`/society-builder/opportunities/intelligence${id ? `?society_id=${id}${debug ? "&debug=true" : ""}` : `${debug ? "?debug=true" : ""}`}`);

export const getDecisionSupport = (id, debug = false) => get(`/society-builder/decision-support${id ? `?society_id=${id}${debug ? "&debug=true" : ""}` : `${debug ? "?debug=true" : ""}`}`);

export const getExecutionPlans = (id, debug = false) => get(`/society-builder/execution-plans${id ? `?society_id=${id}${debug ? "&debug=true" : ""}` : `${debug ? "?debug=true" : ""}`}`);

export const getExecutionIntelligence = (id, debug = false) => get(`/society-builder/execution-intelligence${id ? `?society_id=${id}${debug ? "&debug=true" : ""}` : `${debug ? "?debug=true" : ""}`}`);
export const getInstitutionalMemory = (id, debug = false, search = "") => get(`/society-builder/institutional-memory${id ? `?society_id=${id}${debug ? "&debug=true" : ""}${search ? `&search=${encodeURIComponent(search)}` : ""}` : `${debug || search ? `?${[debug ? "debug=true" : "", search ? `search=${encodeURIComponent(search)}` : ""].filter(Boolean).join("&")}` : ""}`}`);
export const getInstitutionalLearning = (id, debug = false) => get(`/society-builder/institutional-learning${id ? `?society_id=${id}${debug ? "&debug=true" : ""}` : `${debug ? "?debug=true" : ""}`}`);

export const runIntelligenceHealthDiagnostic = () => post("/admin/intelligence-health/run", {});
export const getIntelligenceHealthHistory = () => get("/admin/intelligence-health/history");
