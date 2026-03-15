/**
 * 场景管理类
 * 管理游戏场景、方块、相机
 */

import { Block } from '../level/Block.js';

export class Scene {
    constructor() {
        this.container = null;
        this.blocks = [];
        this.cameraX = 0;
        this.game = null;
    }

    create() {
        // 创建场景容器
        this.container = new Laya.Sprite();
        Laya.stage.addChild(this.container);
        
        // 创建背景
        this.createBackground();
        
        console.log('🌍 场景已创建');
    }

    createBackground() {
        const bg = new Laya.Sprite();
        bg.graphics.drawRect(0, 0, Laya.stage.width, Laya.stage.height, "#87CEEB");
        this.container.addChild(bg);
        
        // 添加云朵装饰
        this.addCloud(100, 100);
        this.addCloud(400, 150);
        this.addCloud(700, 80);
    }

    addCloud(x, y) {
        const cloud = new Laya.Sprite();
        cloud.graphics.drawCircle(0, 0, 30, "#FFFFFF");
        cloud.graphics.drawCircle(25, 0, 35, "#FFFFFF");
        cloud.graphics.drawCircle(50, 0, 30, "#FFFFFF");
        cloud.x = x;
        cloud.y = y;
        this.container.addChild(cloud);
    }

    addBlock(block) {
        this.blocks.push(block);
        this.container.addChild(block.sprite);
    }

    removeBlock(block) {
        const index = this.blocks.indexOf(block);
        if (index > -1) {
            this.blocks.splice(index, 1);
            if (block.sprite && block.sprite.parent) {
                this.container.removeChild(block.sprite);
            }
        }
    }

    clearBlocks() {
        for (let block of this.blocks) {
            if (block.sprite && block.sprite.parent) {
                this.container.removeChild(block.sprite);
            }
        }
        this.blocks = [];
    }

    updateCamera(targetX) {
        // 相机跟随玩家
        const targetCameraX = -targetX + Laya.stage.width / 3;
        this.cameraX = this.lerp(this.cameraX, targetCameraX, 0.1);
        this.container.x = this.cameraX;
    }

    lerp(start, end, t) {
        return start + (end - start) * t;
    }

    destroy() {
        this.clearBlocks();
        if (this.container && this.container.parent) {
            this.container.parent.removeChild(this.container);
        }
    }
}
