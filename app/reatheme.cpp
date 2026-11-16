#include <QApplication>
#include <QWidget>
#include <QPainter>
#include <QPainterPath>
#include <QKeyEvent>
#include <QMouseEvent>
#include <QCloseEvent>
#include <QJsonDocument>
#include <QJsonObject>
#include <QFile>
#include <QDir>
#include <QProcess>
#include <QTimer>
#include <QScreen>
#include <QVariantAnimation>
#include <QLockFile>
#include <QStandardPaths>
#include <QFontDatabase>
#include <algorithm>

static QString read(const QString &path) { QFile f(path); return f.open(QIODevice::ReadOnly) ? QString::fromUtf8(f.readAll()).trimmed() : QString(); }
struct Theme { QString id, title, subtitle, label; QColor accent; QImage image; double focus; };

class REATheme : public QWidget {
public:
    QString package, active, message;
    QVector<Theme> themes;
    int selected=0, previous=0;
    bool busy=false, managing=false, success=false;
    qreal transition=1;
    QProcess process;
    QVariantAnimation motion;
    QVector<QPainterPath> cards;
    QRectF manageButton, applyButton;
    QStringList pending;

    explicit REATheme(QString root):package(std::move(root)) {
        setWindowTitle("REATheme"); setObjectName("REATheme");
        setWindowFlags(Qt::Window | Qt::FramelessWindowHint);
        setAttribute(Qt::WA_OpaquePaintEvent);
        setFocusPolicy(Qt::StrongFocus); setMouseTracking(true);
        setAccessibleName("REATheme 主题选择器");
        QJsonObject profiles=QJsonDocument::fromJson(read(package+"/profiles.json").toUtf8()).object();
        QStringList order={"mosslight","dragonball","bleach","gundam","pacific-rim","halo-fusion","goku-mature"};
        QList<double> focus={.50,.83,.82,.51,.52,.50,.52};
        QStringList shortTitle={"苔光","龙珠","死神","高达","环太平洋","融合机甲","超级赛亚人"};
        QStringList subtitle={"雨夜庭院","金色气焰","月下斩魄","钢铁凝视","核心觉醒","光环 × 环太平洋","超赛觉醒"};
        for(int i=0;i<order.size();++i) {
            auto id=order[i]; auto p=profiles[id].toObject();
            QString wall=package+(id=="mosslight" ? "/wallpaper.png" : "/variants/"+id+"/wallpaper.png");
            QImage img(wall);
            themes.append({id,shortTitle[i],subtitle[i],id=="mosslight" ? "MOSS" : p["label"].toString(),QColor("#"+(id=="mosslight" ? QString("b4c398") : p["accent"].toString())),img.scaledToHeight(900,Qt::SmoothTransformation),focus[i]});
        }
        refresh(); previous=selected;
        motion.setDuration(170); motion.setStartValue(0.0); motion.setEndValue(1.0); motion.setEasingCurve(QEasingCurve::OutCubic);
        connect(&motion,&QVariantAnimation::valueChanged,this,[this](QVariant v){transition=v.toReal();update();});
        process.setProcessChannelMode(QProcess::MergedChannels);
        connect(&process,&QProcess::errorOccurred,this,[this](QProcess::ProcessError e){if(e==QProcess::FailedToStart){busy=false;if(managing){managing=false;showFullScreen();activateWindow();setFocus();}message="无法启动主题引擎，请在管理菜单中检查安装。";update();}});
        connect(&process,qOverload<int,QProcess::ExitStatus>(&QProcess::finished),this,[this](int code,QProcess::ExitStatus status){
            busy=false;
            if(managing){managing=false;refresh();showFullScreen();activateWindow();setFocus();update();return;}
            const QString output=QString::fromUtf8(process.readAll());
            if(code==0 && status==QProcess::NormalExit && read(state()+"/active")==themes[selected].id){
                active=themes[selected].id;success=true;message="已应用 · "+themes[selected].title+" / "+themes[selected].subtitle;
                QTimer::singleShot(650,this,&QWidget::close);
            } else {message="应用失败，已尝试回退。"+output.right(200).simplified();}
            update();
        });
    }
    QString state() const {return QDir::homePath()+"/.local/state/mosslight";}
    void refresh(){active=read(state()+"/active");for(int i=0;i<themes.size();++i)if(themes[i].id==active)selected=i;}
    QFont fontFor(int size,bool mono=false,int weight=QFont::Normal) const {
        QFont f(mono ? "monospace" : "Alibaba PuHuiTi 3.0"); f.setPixelSize(size); f.setWeight(QFont::Weight(weight));return f;
    }
    void choose(int index){
        if(busy || success)return;
        index=(index+themes.size())%themes.size();if(index==selected)return;
        previous=selected;selected=index;message.clear();motion.stop();motion.start();
        setAccessibleDescription(themes[selected].title+"，"+themes[selected].subtitle+"。回车应用，左右方向键切换。");
    }
    void applySelection(){
        if(busy||success)return;
        if(themes[selected].image.isNull()){message="壁纸缺失，无法应用此主题。";update();return;}
        busy=true;message="正在更换壁纸、顶栏、窗口、锁屏、图标与登录页…";update();
        process.start("python3",{package+"/theme.py","apply",themes[selected].id});
    }
    void manage(){if(busy||success)return;managing=true;busy=true;hide();process.start("python3",{package+"/theme.py","manage"});}
    void paintEvent(QPaintEvent*) override {
        QPainter p(this);p.setRenderHints(QPainter::Antialiasing|QPainter::SmoothPixmapTransform|QPainter::TextAntialiasing);
        const qreal w=width(),h=height(),margin=std::max(22.,w*.025),step=(w-2*margin)/themes.size();
        const qreal ch=std::clamp(h*.395,250.,440.),top=(h-ch)/2+8;
        auto accent=themes[selected].accent;
        p.fillRect(rect(),QColor("#0c1013"));
        QRadialGradient glow(w*.53,h*.5,w*.6);QColor gc=accent;gc.setAlpha(20);glow.setColorAt(0,gc);glow.setColorAt(1,QColor(0,0,0,0));p.fillRect(rect(),glow);
        // Sparse construction lines keep the wallpaper cards as the focal point.
        p.setPen(QColor("#1a2227"));p.drawLine(QPointF(margin,top-80),QPointF(w-margin,top-80));p.drawLine(QPointF(margin,top+ch+88),QPointF(w-margin,top+ch+88));
        p.setFont(fontFor(36,false,QFont::Medium));p.setPen(QColor("#e5e7e1"));p.drawText(QPointF(margin,top-112),"REATheme");
        p.setFont(fontFor(10,true));p.setPen(QColor("#67777d"));p.drawText(QPointF(margin+224,top-114),"PERSONAL THEME COLLECTION");
        p.setFont(fontFor(12));p.setPen(QColor("#99a5a7"));p.drawText(QRectF(w-margin-330,top-141,330,32),Qt::AlignRight|Qt::AlignVCenter,"壁纸与全套桌面组件 · 一次切换");
        cards.clear();
        for(int i=0;i<themes.size();++i){
            const auto &t=themes[i];qreal amount=i==selected ? transition : (i==previous ? 1-transition : 0);
            qreal x=margin+i*step,y=top-amount*14,cw=step-7,hh=ch+amount*28,slant=std::min(38.,cw*.18);
            QPolygonF polygon;polygon<<QPointF(x+slant,y)<<QPointF(x+cw,y)<<QPointF(x+cw-slant,y+hh)<<QPointF(x,y+hh);
            QPainterPath path;path.addPolygon(polygon);path.closeSubpath();cards.append(path);
            p.save();p.setClipPath(path);p.fillPath(path,QColor("#1c2427"));
            if(!t.image.isNull()){
                qreal sourceWidth=t.image.height()*cw/hh;
                qreal sx=std::clamp(t.image.width()*t.focus-sourceWidth/2,0.,std::max(0.,t.image.width()-sourceWidth));
                p.drawImage(QRectF(x,y,cw,hh),t.image,QRectF(sx,0,sourceWidth,t.image.height()));
            }
            p.fillPath(path,QColor(6,10,12,int(94-amount*72)));
            QLinearGradient shade(0,y+hh*.42,0,y+hh);shade.setColorAt(0,QColor(7,12,15,0));shade.setColorAt(.6,QColor(7,12,15,150));shade.setColorAt(1,QColor(7,12,15,248));p.fillPath(path,shade);
            p.setPen(t.accent);p.setFont(fontFor(10,true));p.drawText(QPointF(x+slant+12,y+26),QString("%1 / %2").arg(i+1,2,10,QChar('0')).arg(t.label));
            const qreal tx=x+18,tw=cw-slant-27;
            p.setFont(fontFor(step<180?16:21,false,QFont::Medium));p.setPen(i==selected?QColor("#f0f1e9"):QColor("#b9c3c1"));
            p.drawText(QRectF(tx,y+hh-94,tw,30),Qt::AlignLeft|Qt::AlignVCenter,t.title);
            p.setFont(fontFor(step<180?10:12));p.setPen(t.accent);p.drawText(QRectF(tx,y+hh-60,tw,22),Qt::AlignLeft|Qt::AlignVCenter,t.subtitle);
            if(t.id==active){p.setFont(fontFor(9,true));p.setPen(QColor("#cad4ce"));p.drawText(QPointF(tx,y+hh-18),"●  CURRENT");}
            p.restore();p.setBrush(Qt::NoBrush);p.setPen(QPen(i==selected ? t.accent : QColor("#303b3f"),i==selected?1.5:0.7));p.drawPath(path);
            if(i==selected){p.setPen(QPen(t.accent,3));p.drawLine(QPointF(x+slant+1,y+1),QPointF(x+slant+42,y+1));}
        }
        p.setFont(fontFor(14));p.setPen(accent);p.drawText(QPointF(margin,top+ch+64),QString("%1  /  %2").arg(themes[selected].title,themes[selected].subtitle));
        p.setFont(fontFor(11,true));p.setPen(QColor("#84958f"));p.drawText(QRectF(w-margin-120,top+ch+42,120,28),Qt::AlignRight|Qt::AlignVCenter,QString("%1  /  07").arg(selected+1,2,10,QChar('0')));
        p.setFont(fontFor(12));p.setPen(QColor("#96a5a7"));p.drawText(QPointF(margin,top+ch+125),"←  →  选择主题       Enter  应用整套主题       Esc  退出");
        manageButton=QRectF(w-margin-140,top+ch+103,140,34);p.setPen(QColor("#94a39e"));p.drawText(manageButton,Qt::AlignRight|Qt::AlignVCenter,"管理 / 回退   F2");
        applyButton=QRectF(margin,top+ch+40,w-2*margin-160,40);
        if(!message.isEmpty()){
            p.fillRect(QRectF(margin,top+ch+148,w-2*margin,60),QColor("#0c1013"));p.setFont(fontFor(12));p.setPen(success?accent:QColor("#c8ceca"));p.drawText(QRectF(margin,top+ch+150,w-2*margin,56),Qt::TextWordWrap,message);
        }
        if(busy&&!managing){p.setPen(QPen(accent,2));p.drawLine(QPointF(margin,top+ch+89),QPointF(w-margin,top+ch+89));}
    }
    void keyPressEvent(QKeyEvent *e) override {
        if(busy||success){e->accept();return;}
        switch(e->key()){
            case Qt::Key_Right:case Qt::Key_Down:choose(selected+1);break;
            case Qt::Key_Left:case Qt::Key_Up:choose(selected-1);break;
            case Qt::Key_Home:choose(0);break;case Qt::Key_End:choose(themes.size()-1);break;
            case Qt::Key_Return:case Qt::Key_Enter:applySelection();break;
            case Qt::Key_Escape:close();break;case Qt::Key_F2:manage();break;
            default:if(e->key()>=Qt::Key_1&&e->key()<=Qt::Key_7)choose(e->key()-Qt::Key_1);else QWidget::keyPressEvent(e);
        }
    }
    void mousePressEvent(QMouseEvent *e) override {
        if(busy||success)return;
        if(manageButton.contains(e->position())){manage();return;}
        if(applyButton.contains(e->position())){applySelection();return;}
        for(int i=0;i<cards.size();++i)if(cards[i].contains(e->position())){choose(i);return;}
    }
    void mouseDoubleClickEvent(QMouseEvent *e) override {for(int i=0;i<cards.size();++i)if(cards[i].contains(e->position())){choose(i);applySelection();return;}}
    void closeEvent(QCloseEvent *e) override {if(busy)e->ignore();else e->accept();}
};

#ifndef REATHEME_TEST
int main(int argc,char **argv){
    QApplication app(argc,argv);app.setApplicationName("REATheme");app.setDesktopFileName("REATheme");
    QLockFile lock(QStandardPaths::writableLocation(QStandardPaths::RuntimeLocation)+"/reatheme-ui.lock");lock.setStaleLockTime(0);
    if(!lock.tryLock(0))return 0;
    QString package=QDir(QCoreApplication::applicationDirPath()+"/..").absolutePath();
    REATheme window(package);window.showFullScreen();window.activateWindow();window.setFocus();
    return app.exec();
}
#endif
