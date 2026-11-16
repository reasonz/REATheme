#define REATHEME_TEST
#include "reatheme.cpp"
#include <QtTest/QTest>
#include <QTemporaryDir>
#include <QElapsedTimer>
#include <iostream>

static void require(bool ok,const char *message){if(!ok){std::cerr<<message<<std::endl;std::exit(1);}}
int main(int argc,char **argv){
    QApplication app(argc,argv);
    require(argc>=3,"usage: verify PACKAGE OUTPUT.png [--live]");
    REATheme window(argv[1]);window.resize(1920,1080);window.show();window.setFocus();QTest::qWait(200);
    const int initial=window.selected;
    QTest::keyClick(&window,Qt::Key_Right);require(window.selected==(initial+1)%7,"Right key failed");
    QTest::keyClick(&window,Qt::Key_Left);require(window.selected==initial,"Left key failed");
    QTest::keyClick(&window,Qt::Key_Home);QTest::keyClick(&window,Qt::Key_Left);require(window.selected==6,"Left wrap failed");
    QTest::keyClick(&window,Qt::Key_Right);require(window.selected==0,"Right wrap failed");
    QTest::keyClick(&window,Qt::Key_4);require(window.selected==3,"Direct selection failed");
    QTest::qWait(200);require(window.grab().save(argv[2]),"Screenshot failed");
    window.resize(1280,720);QTest::qWait(80);require(window.grab().save(QString(argv[2])+"-1280.png"),"Small screenshot failed");
    for(const auto &path:window.cards)require(path.boundingRect().left()>=0 && path.boundingRect().right()<=1280,"Card exceeds screen");
    window.choose(initial);QTest::qWait(200);
    if(argc>3 && QString(argv[3])=="--live"){
        // Keep the offscreen rendering platform out of real desktop child processes.
        qunsetenv("QT_QPA_PLATFORM");
        QTest::keyClick(&window,Qt::Key_Return);require(window.busy,"Return did not start applying");
        QTest::keyClick(&window,Qt::Key_Escape);require(window.isVisible(),"Escape interrupted active transaction");
        QElapsedTimer timer;timer.start();while(window.busy&&timer.elapsed()<20000)QTest::qWait(50);
        require(window.success,"Live theme application failed");
        require(window.active==window.themes[initial].id,"Applied wrong theme");
    }else{
        QTest::keyClick(&window,Qt::Key_Escape);require(!window.isVisible(),"Escape did not close");
    }
    std::cout<<"PASS: arrows, wrap, numeric selection, image rendering, 1280 layout, "<<(argc>3?"Enter and complete theme transaction":"Escape")<<std::endl;
}
