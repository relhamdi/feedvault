/**
 * Create backdrop event handlers for modals.
 * Prevents closing when user clicks inside and drags outside.
 */
export function createBackdropHandlers(onClose) {
    let mouseDownOnBackdrop = false;

    return {
        handleMouseDown(e) {
            mouseDownOnBackdrop = e.target === e.currentTarget;
        },
        handleClick(e) {
            if (mouseDownOnBackdrop && e.target === e.currentTarget) onClose();
            mouseDownOnBackdrop = false;
        },
        handleKeydown(e) {
            if (e.key === 'Escape') onClose();
        },
    };
}
