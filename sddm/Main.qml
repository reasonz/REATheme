import QtQuick
import QtQuick.Controls.Basic

Rectangle {
    id: root
    width: 1920; height: 1080
    color: config.stringValue("bg")
    property color ink: config.stringValue("fg")
    property color accent: config.stringValue("accent")
    property color panel: config.stringValue("panel")
    property color line: config.stringValue("border")
    property color muted: config.stringValue("muted")
    property bool busy: false
    property string clockText: Qt.formatDateTime(new Date(), "hh:mm")
    function login() {
        if (busy || !username.text.length) return
        busy = true
        feedback.text = "正在验证…"
        sddm.login(username.text, password.text, session.currentIndex)
    }
    Image { anchors.fill: parent; source: config.stringValue("background"); fillMode: Image.PreserveAspectCrop }
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "#ed101418" }
            GradientStop { position: 0.40; color: "#b0101418" }
            GradientStop { position: 0.75; color: "#18101418" }
        }
    }
    Rectangle { x: 0; y: 0; width: parent.width; height: 1; color: root.accent }
    Text { x: 48; y: 24; text: config.stringValue("title") + "  /  ACCESS"; color: root.accent; font.family: "monospace"; font.pixelSize: 12; font.letterSpacing: 2 }
    Text { anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 24; text: Qt.formatDate(new Date(), "yyyy.MM.dd"); color: root.ink; font.family: "monospace"; font.pixelSize: 12 }
    Column {
        x: Math.max(48, root.width * 0.065)
        y: Math.max(90, (root.height - height) / 2)
        width: 320; spacing: 14
        Text { text: root.clockText; color: root.ink; font.family: "monospace"; font.pixelSize: 68; font.weight: Font.Light }
        Text { text: config.stringValue("subtitle"); color: root.accent; font.family: "Alibaba PuHuiTi 3.0"; font.pixelSize: 14 }
        Rectangle { width: 40; height: 1; color: root.accent }
        Item { width: 1; height: 10 }
        TextField {
            id: username; width: parent.width; height: 40
            text: userModel.lastUser; placeholderText: "用户名"
            color: root.ink; placeholderTextColor: root.muted
            font.family: "monospace"; font.pixelSize: 13
            leftPadding: 12; enabled: !root.busy
            background: Rectangle { color: "#d0101418"; border.width: 1; border.color: username.activeFocus ? root.accent : root.line }
            onAccepted: password.forceActiveFocus()
            KeyNavigation.tab: password
        }
        TextField {
            id: password; width: parent.width; height: 40
            placeholderText: "密码"; echoMode: TextInput.Password
            color: root.ink; placeholderTextColor: root.muted
            font.family: "monospace"; font.pixelSize: 13
            leftPadding: 12; enabled: !root.busy
            background: Rectangle { color: "#d0101418"; border.width: 1; border.color: password.activeFocus ? root.accent : root.line }
            onAccepted: root.login()
            KeyNavigation.tab: session
        }
        ComboBox {
            id: session; width: parent.width; height: 34
            model: sessionModel; textRole: "name"; currentIndex: sessionModel.lastIndex
            font.family: "monospace"; font.pixelSize: 11
            palette.text: root.ink; palette.buttonText: root.ink; palette.base: root.panel; palette.highlight: root.line; palette.highlightedText: root.accent
            contentItem: Text { text: session.displayText; color: root.muted; font: session.font; verticalAlignment: Text.AlignVCenter; leftPadding: 12 }
            background: Rectangle { color: "#c0101418"; border.color: root.line; border.width: 1 }
            KeyNavigation.tab: enter
        }
        Button {
            id: enter; width: parent.width; height: 40; text: root.busy ? "验证中…" : "进入桌面  →"; enabled: !root.busy
            contentItem: Text { text: enter.text; color: root.accent; font.family: "Alibaba PuHuiTi 3.0"; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: enter.hovered ? root.line : root.panel; border.width: 1; border.color: root.accent }
            onClicked: root.login()
        }
        Text { id: feedback; width: parent.width; height: 24; text: keyboard.capsLock ? "Caps Lock 已开启" : ""; color: root.muted; font.family: "Alibaba PuHuiTi 3.0"; font.pixelSize: 12; wrapMode: Text.WordWrap }
    }
    Text { x: 48; anchors.bottom: parent.bottom; anchors.bottomMargin: 24; text: "REATHEME  /  " + sddm.hostName; color: root.muted; font.family: "monospace"; font.pixelSize: 10; font.letterSpacing: 1 }
    Row {
        anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 24; spacing: 18
        Button { text: "重新启动"; font.family: "Alibaba PuHuiTi 3.0"; visible: sddm.canReboot; palette.buttonText: root.ink; flat: true; onClicked: sddm.reboot() }
        Button { text: "关机"; font.family: "Alibaba PuHuiTi 3.0"; visible: sddm.canPowerOff; palette.buttonText: root.ink; flat: true; onClicked: sddm.powerOff() }
    }
    Timer { interval: 1000; running: true; repeat: true; onTriggered: root.clockText = Qt.formatDateTime(new Date(), "hh:mm") }
    Connections {
        target: sddm
        function onLoginFailed() { root.busy = false; password.text = ""; feedback.text = "登录失败，请检查用户名和密码"; password.forceActiveFocus() }
        function onLoginSucceeded() { password.text = ""; feedback.text = "正在进入桌面…" }
    }
    Component.onCompleted: { if (username.text.length) password.forceActiveFocus(); else username.forceActiveFocus() }
}
