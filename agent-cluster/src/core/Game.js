/**
 * 游戏主类
 * 管理游戏状态、场景、更新循环
 */

import { Scene } from './Scene.js';
import { Player } from '../player/Player.js';
import { LevelGenerator } from '../level/LevelGenerator.js';
import { HUD } from '../ui/HUD.js';
import { StartScreen } from '../ui/StartScreen.js';
import { GameOver } from '../ui/GameOver.js';
import { AudioManager } from '../audio/AudioManager.js';

export class Game {
    constructor() {
        this.state = 'start'; // start, playing, gameover
        this.score = 0;
        this.scene = null;
        this.player = null;
        this.levelGenerator = null;
        this.hud = null;
        this.startScreen = null;
        this.gameOver = null;
        this.audioManager = null;
    }

    start() {
        console.log('🎮 游戏启动');
        
        // 初始化各系统
        this.audioManager = new AudioManager();
        this.levelGenerator = new LevelGenerator();
        
        // 创建 UI
        this.startScreen = new StartScreen(() => this.onGameStart());
        this.hud = new HUD();
        this.gameOver = new GameOver(() => this.onRestart());
        
        // 初始显示开始界面
        this.showStartScreen();
    }

    onGameStart() {
        console.log('🎯 游戏开始');
        this.state = 'playing';
        this.score = 0;
        
        // 隐藏开始界面
        this.startScreen.hide();
        
        // 创建游戏场景
        this.scene = new Scene();
        this.scene.create();
        
        // 创建玩家
        this.player = new Player(this.scene);
        this.player.create();
        
        // 生成初始关卡
        this.levelGenerator.generateInitialLevel(this.scene);
        
        // 更新 HUD
        this.hud.updateScore(0);
        this.hud.show();
        
        // 开始游戏循环
        Laya.timer.frameLoop(1, this, this.gameLoop);
    }

    onRestart() {
        console.log('🔄 重新开始');
        this.gameOver.hide();
        this.onGameStart();
    }

    gameLoop() {
        if (this.state !== 'playing') return;
        
        // 更新玩家
        this.player.update();
        
        // 检查碰撞
        this.checkCollisions();
        
        // 检查失败条件
        this.checkGameOver();
    }

    checkCollisions() {
        if (!this.player || !this.scene) return;
        
        // 检测玩家与方块的碰撞
        const blocks = this.scene.blocks;
        const playerRect = this.player.getBounds();
        
        for (let block of blocks) {
            const blockRect = block.getBounds();
            if (this.intersects(playerRect, blockRect)) {
                this.onLandOnBlock(block);
                break;
            }
        }
    }

    onLandOnBlock(block) {
        if (block.passed) return; // 已经得分的方块
        
        block.passed = true;
        this.score++;
        this.hud.updateScore(this.score);
        this.audioManager.play('score');
        
        // 生成新方块
        this.levelGenerator.generateNextBlock(this.scene);
        
        // 检查是否是完美落地
        if (this.isPerfectLand(block)) {
            this.score += 1; // 额外加分
            this.hud.updateScore(this.score);
            this.hud.showPerfect();
        }
    }

    isPerfectLand(block) {
        // 检测是否落在方块中心
        const playerX = this.player.x;
        const blockCenter = block.x + block.width / 2;
        const distance = Math.abs(playerX - blockCenter);
        return distance < block.width * 0.2; // 中心 20% 区域
    }

    checkGameOver() {
        if (!this.player || !this.scene) return;
        
        // 玩家掉落检测
        if (this.player.y > Laya.stage.height + 100) {
            this.onGameOver();
        }
    }

    onGameOver() {
        console.log('💀 游戏结束');
        this.state = 'gameover';
        Laya.timer.clear(this, this.gameLoop);
        this.audioManager.play('gameover');
        this.gameOver.show(this.score);
        this.hud.hide();
    }

    showStartScreen() {
        this.startScreen.show();
    }

    intersects(rect1, rect2) {
        return rect1.x < rect2.x + rect2.width &&
               rect1.x + rect1.width > rect2.x &&
               rect1.y < rect2.y + rect2.height &&
               rect1.y + rect1.height > rect2.y;
    }
}
