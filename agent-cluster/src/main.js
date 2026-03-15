/**
 * 跳一跳游戏 - 主入口
 * 引擎：LayaAir 3.3.8 (2D)
 */

// 游戏配置
const GameConfig = {
    width: 750,
    height: 1334,
    bgColor: "#87CEEB",
    fps: 60
};

// 初始化 LayaAir
Laya.init(GameConfig.width, GameConfig.height, Laya.WebGL);
Laya.stage.bgColor = GameConfig.bgColor;
Laya.stage.scaleMode = Laya.Stage.SCALE_SHOWALL;
Laya.stage.alignH = Laya.Stage.ALIGN_CENTER;
Laya.stage.alignV = Laya.Stage.ALIGN_MIDDLE;
Laya.stage.frameRate = GameConfig.fps;

// 导入游戏模块
import { Game } from './core/Game.js';

// 启动游戏
const game = new Game();
game.start();

console.log('🎮 跳一跳游戏已启动');
