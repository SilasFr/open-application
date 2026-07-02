"use client";

import type { Application } from "@/lib/api";
import NotesTimeline from "@/components/NotesTimeline";

interface ApplicationDetailPanelProps {
  application: Application;
  onClose: () => void;
}

/** Slide-over with an application's timeline, contacts, and tasks.
 * Contacts/Tasks sections are added by later user stories (US3/US4). */
export default function ApplicationDetailPanel({
  application,
  onClose,
}: ApplicationDetailPanelProps) {
  return (
    <div className="fixed inset-0 z-20 flex justify-end">
      <button
        aria-label="Close"
        onClick={onClose}
        className="flex-1 bg-black/30"
      />
      <div className="h-full w-full max-w-md overflow-y-auto border-l border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-black">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">{application.role}</h2>
            <p className="text-sm text-gray-500">{application.company}</p>
          </div>
          <button
            onClick={onClose}
            className="text-sm text-gray-500 hover:underline"
          >
            Close
          </button>
        </div>

        <div className="mt-4">
          <NotesTimeline applicationId={application.id} />
        </div>
      </div>
    </div>
  );
}
