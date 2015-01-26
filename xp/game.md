*todo:
impactjs
create.js (adobe)



Construct2、ImactJS、LimeJS、GameMaker、CreateJS、lycheeJS、Crafty、three.js、melonJS、Turbulenz、Quintus、Cocos2d-html5

<resource>
http://blog.csdn.net/zhaoxy_thu/article/details/11867123
http://www.jsbreakouts.org/
http://html5gameengine.com/

</resource>

<cosmic>
* 是否一开始load了太多资源



console.log();


            PetPreLoader.preload(g_ressources_MainMap, function () {
                Scene_MainMap.changeTo();
            }, this);


*
cc.GameApplication (main.js 主入口)
    _StartGame (GameClasses/GameManager.js)
        Scene_Loading.createToMainMenu (GameScenes/Scene_Loading.js)
            Scene_Loading.create
                LoadHandler_ToMainMenu

startGame (开始游戏, GUI/GUIMainMenu.js 主界面)
    Scene_MainMap.changeTo
        Scene_MainMap.create (GameScenes/Scene_MainMap.js 主地图)

_btnStartGameCallback (每关里面的开始游戏，GUI/GUIGameLevel/GUIGameLevelStart.js)


onEnter (Scene_MainMap.js)
    update (GUI/GUIMap/GUIMapMng.js, 读取最大关)


Scene_MainMap.changeTo
    LoadHandler_ToGameLevel


DisplayLinkDirector.mainLoop (CCDirector.js)
    CC.Director.drawScene
        Scheduler.update (CCScheduler.js)
            Timer.update
                Scene_GameLevel.update (SceneGameLevel.js)
                    GameStateWrapper.update
                        cc.IStateWrapper.update
                            State_GameLevel.update
                                GameLevel.handleFinish
                                    GameLevel.gameLevelSuccess （很炫的效果， GameLevel.js)
                                        State_GameCarnivalUnlockAndDestroy.create
                                            Cmd_LeftMovesToBombWrapMonster.start
                                                Cmd_LeftMovesToBombWrapMonster.create(this.m_Moves) (剩余的步数等于炸弹的数量, Commands/Cmd_CarnivalUnlockAndDestroy.js)

        setNextScene
            _runningScene.onEnter
                GameStateWrapper.changeTo (GameStateWrapper.js)


State_GameLevel.


cc.Director.getInstance().replaceScene()
map: TileMaps/ 初始化的
GameLevelData.js

GameClasses/ResourceMng.js


Defines.TARGET_MODEL.MODEL_DESTROY

GUI/GUIGameLevel/GUIGameLevelEndWin.js

gameLevelSuccess (GameClasses/GameLevel.js)

space level 挑战关卡

修改前: createCount 162

src/Effect/Effect_BezierPath.js 2
src/Effect/Effect_NotifyTarget.js 2
src/GUI/GUIGameLevel/GUIGameLevelItem.js 1
src/GUI/GUIGameLevel/GUIGameLevelProgress.js


all: 72
xiaoguailizi-a 10 (都可以重用)
daojulizi (tailerParticle, outter) 28
daojuguangdian (spriteBezierParticle, inner) 28
star_explode_particle 3 (都可以重用)
item_prompt_particle 3 还没有重用

问题：
1. 一开始load资源比较多。
2. 增加particle system pool
3. particle system内存占用多。可以考虑一个pool。目前的tailer和spirit的粒子系统耦合，是否可以解耦，从而让生存周期尽量不overlap。

* 每一帧

cc.Application
    cc.DisplayLinkDirector.mainLoop
        drawScene
            cc.scheduler.update
                cc.ActionManager.update
            setNextScene // 切换场景
                cc.Scene.onEnter


* armature会建立pool
Armature/Armature_Monster.js

*

GameClasses/GameManager.js 总体管理游戏
Scene_GameLevel 每关的scene

Scene_GameLevel.changeTo
    LoadHandler_ToGameLevel.create
    LoadHandler_ToGameLevel.update
        Scene_GameLevel.create
        Scene_GameLevel.update


</cosmic>

<cocos2d-js>
* canvas or webgl
CCBoot.js
cc._renderType: cc._RENDER_TYPE_WEBGL

*
cc.game.run (总入口, main.js)
    cc.game.onStart

cc.director.runScene

"5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36"
</cocos2d-js>

<three.js>
右手坐标系
支持WebGL, Canvas2D和SVG
用于画3D，不是一个游戏引擎

</three.js>

<unity>
* webgl benchmark有code，但是不开源
http://files.unity3d.com/jonas/WebGLBenchmarksSource.zip
</unity>

<egret>
* 使用typescript
* 接近flash

</egret>

<playcanvas>


</playcanvas>

<construct2>
* only windows
可以不用编程
* scirra
</construct2>