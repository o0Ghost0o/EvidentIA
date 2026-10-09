/**
 * Alias endpoint for /api/chat forwarding directly to /api/copilot.
 * Ensures compatibility with AI SDK default /api/chat path and external integrations.
 */
import copilotHandler from "./copilot.post";

export default copilotHandler;
