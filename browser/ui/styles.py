"""Dark incognito theme."""

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #202124;
    color: #e8eaed;
    font-family: "Segoe UI", system-ui, sans-serif;
    font-size: 13px;
}

#toolbar {
    background-color: #292a2d;
    border-bottom: 1px solid #3c4043;
    padding: 6px 8px;
    spacing: 6px;
}

#navBtn {
    background-color: transparent;
    border: none;
    border-radius: 16px;
    padding: 0;
    margin: 0;
    min-width: 32px;
    min-height: 32px;
    max-width: 32px;
    max-height: 32px;
}

#navBtn:hover { background-color: #3c4043; }
#navBtn:pressed { background-color: #5f6368; }
#navBtn:disabled { opacity: 0.35; }

#addressBar {
    background-color: #303134;
    border: 1px solid #5f6368;
    border-radius: 20px;
    padding: 6px 16px;
    color: #e8eaed;
    selection-background-color: #8ab4f8;
    selection-color: #202124;
}

#addressBar:focus {
    border-color: #8ab4f8;
    background-color: #35363a;
}

#starBtn {
    background-color: transparent;
    border: none;
    border-radius: 16px;
    color: #f9ab00;
    font-size: 18px;
    padding: 0;
}
#starBtn:hover { background-color: #3c4043; }

#shieldBtn {
    background-color: transparent;
    border: none;
    border-radius: 14px;
    color: #9aa0a6;
    font-size: 12px;
    padding: 0 10px;
    min-height: 28px;
}
#shieldBtn:hover { background-color: #3c4043; color: #8ab4f8; }

#blockCountLabel { color: #8ab4f8; }

#tabRow {
    background-color: #202124;
    border-bottom: 1px solid #3c4043;
    min-height: 32px;
    max-height: 32px;
}

#tabStack { background-color: #202124; border: none; }

#mainTabBar {
    background-color: transparent;
    border: none;
    padding: 0;
    margin: 0;
    font-size: 12px;
}

#mainTabBar::tab {
    background-color: #292a2d;
    color: #9aa0a6;
    border: none;
    border-right: 1px solid #3c4043;
    border-top: 1px solid transparent;
    border-radius: 0;
    padding: 4px 24px 4px 10px;
    margin: 0;
    min-width: 100px;
    max-width: 200px;
    min-height: 22px;
    max-height: 28px;
}

#mainTabBar::tab:selected {
    background-color: #35363a;
    color: #e8eaed;
    border-top: 1px solid #8ab4f8;
}

#mainTabBar::tab:hover:!selected {
    background-color: #323639;
    color: #e8eaed;
}

#tabCloseBtn {
    background-color: transparent;
    border: none;
    border-radius: 9px;
    padding: 0;
    margin: 0;
    min-width: 18px;
    max-width: 18px;
    min-height: 18px;
    max-height: 18px;
}
#tabCloseBtn:hover { background-color: #5f6368; }
#tabCloseBtn:pressed { background-color: #8ab4f8; }

#newTabBtn {
    background-color: transparent;
    border: none;
    outline: none;
    border-radius: 12px;
    padding: 0;
    margin: 0;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
}
#newTabBtn:hover { background-color: #3c4043; }
#newTabBtn:pressed { background-color: #5f6368; }
#newTabBtn:focus { border: none; outline: none; }

#menuBtn {
    background-color: transparent;
    border: none;
    border-radius: 16px;
    color: #e8eaed;
    font-size: 18px;
    font-weight: bold;
    padding: 0;
    margin: 0;
}
#menuBtn:hover { background-color: #3c4043; }
#menuBtn:pressed { background-color: #5f6368; }

#appMenu, QMenu {
    background-color: #292a2d;
    color: #e8eaed;
    border: 1px solid #3c4043;
    padding: 4px 0;
}
#appMenu::item, QMenu::item { padding: 8px 28px 8px 16px; }
#contextMenu::item { padding: 8px 28px 8px 8px; }
#contextMenu::icon { width: 16px; height: 16px; padding-left: 12px; }
#appMenu::item:selected, QMenu::item:selected { background-color: #3c4043; }

#downloadPanel { background-color: #292a2d; border-top: 1px solid #3c4043; }
#downloadRow { background-color: #292a2d; border-bottom: 1px solid #3c4043; }
#downloadName { color: #e8eaed; font-size: 12px; }
#downloadStatus { color: #9aa0a6; font-size: 12px; }

#downloadProgress {
    background-color: #3c4043;
    border: none;
    border-radius: 4px;
    min-height: 8px;
    max-height: 8px;
    text-align: center;
    color: #e8eaed;
    font-size: 10px;
}
#downloadProgress::chunk { background-color: #8ab4f8; border-radius: 4px; }

#downloadCancelBtn {
    background-color: transparent;
    border: none;
    border-radius: 11px;
    color: #9aa0a6;
    font-size: 14px;
    padding: 0;
}
#downloadCancelBtn:hover { background-color: #5f6368; color: #ffffff; }

#downloadsPage { background-color: #202124; }
#downloadsPageHeader { background-color: #202124; border-bottom: 1px solid #3c4043; }
#downloadsPageTitle { color: #e8eaed; font-size: 22px; font-weight: 400; }
#downloadsEmptyLabel { color: #9aa0a6; font-size: 14px; padding: 48px; }
#downloadsScroll { background-color: #202124; border: none; }
#downloadsListRow { background-color: #292a2d; border-bottom: 1px solid #3c4043; }
#downloadsListTitle { color: #e8eaed; font-size: 14px; font-weight: 500; }
#downloadsListSubtitle { color: #9aa0a6; font-size: 11px; }
#downloadsListStatus { color: #8ab4f8; font-size: 12px; }

#downloadsActionBtn {
    background-color: #3c4043;
    border: none;
    border-radius: 4px;
    color: #e8eaed;
    padding: 6px 12px;
    font-size: 12px;
}
#downloadsActionBtn:hover { background-color: #5f6368; }
#downloadsActionBtn:disabled { color: #5f6368; background-color: #292a2d; }

#findBar { background-color: #292a2d; border-bottom: 1px solid #3c4043; }
#findInput {
    background-color: #303134;
    border: 1px solid #5f6368;
    border-radius: 4px;
    padding: 4px 10px;
    color: #e8eaed;
}
#findStatus { color: #9aa0a6; font-size: 12px; min-width: 80px; }
#findBtn {
    background-color: #3c4043;
    border: none;
    border-radius: 4px;
    color: #e8eaed;
    font-size: 14px;
}
#findBtn:hover { background-color: #5f6368; }

#toast { background-color: #35363a; border: 1px solid #5f6368; border-radius: 8px; }
#toastLabel { color: #e8eaed; font-size: 13px; }

#sessionPage, #sessionPageHeader { background-color: #202124; }
#sessionPageHeader { border-bottom: 1px solid #3c4043; }
#sessionPageTitle { color: #e8eaed; font-size: 22px; }
#sessionEmptyLabel { color: #9aa0a6; font-size: 14px; padding: 48px; }
#sessionScroll { background-color: #202124; border: none; }
#sessionListRow { background-color: #292a2d; border-bottom: 1px solid #3c4043; }
#sessionListTitle { color: #e8eaed; font-size: 14px; }
#sessionListMeta { color: #9aa0a6; font-size: 11px; }

#sessionActionBtn {
    background-color: #3c4043;
    border: none;
    border-radius: 4px;
    color: #e8eaed;
    padding: 6px 12px;
    font-size: 12px;
}
#sessionActionBtn:hover { background-color: #5f6368; }

QToolTip { background-color: #3c4043; color: #e8eaed; border: 1px solid #5f6368; }

#bookmarksBar {
    background-color: #292a2d;
    border-bottom: 1px solid #3c4043;
    min-height: 30px;
    max-height: 30px;
}

#bookmarksBarBtn {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    color: #e8eaed;
    font-size: 12px;
    padding: 3px 10px;
}
#bookmarksBarBtn:hover { background-color: #3c4043; }
#bookmarksBarBtn:pressed { background-color: #5f6368; }

#bookmarksBarEmpty {
    color: #9aa0a6;
    font-size: 12px;
    padding: 0 8px;
}

#devToolsDock {
    background-color: #202124;
    color: #e8eaed;
    border-top: 1px solid #3c4043;
}
#devToolsDock::title {
    background-color: #292a2d;
    padding: 4px 8px;
}

#secLabel { color: #9aa0a6; font-size: 14px; }

#loadStrip {
    background-color: transparent;
    border: none;
    max-height: 3px;
    min-height: 3px;
}
#loadStrip::chunk { background-color: #8ab4f8; }

#shortcutsDialog { background-color: #202124; }
#shortcutsScroll { background-color: #202124; border: none; }
#shortcutsHeader {
    color: #e8eaed;
    font-size: 18px;
    padding: 18px 20px 8px 20px;
    border-bottom: 1px solid #3c4043;
}
#shortcutKey {
    background-color: #3c4043;
    border: 1px solid #5f6368;
    border-radius: 4px;
    color: #e8eaed;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 3px 8px;
}
#shortcutDesc { color: #9aa0a6; font-size: 13px; }
"""
