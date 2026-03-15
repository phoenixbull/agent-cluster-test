/**
 * 玩家角色类
 * 处理跳跃物理、蓄力、动画
 */

import { Input } from './Input.js';

export class Player {
    constructor(scene) {
        this.scene = scene;
        this.sprite = null;
        this.x = 0;
        this.y = 0;
        this.width = 60;
        this.height = 80;
        
        // 物理状态
        this.state = 'idle'; // idle, charging, jumping, falling, landed
        this.chargeTime = 0;
        this.maxChargeTime = 2000; // ms
        this.velocityX = 0;
        this.velocityY = 0;
        this.gravity = 0.5;
        
        // 输入处理
        this.input = new Input(this);
    }

    create() {
        // 创建玩家精灵（使用占位图形）
        this.sprite = new Laya.Sprite();
        
        // 绘制角色（临时使用矩形）
        const graphics = this.sprite.graphics;
        graphics.drawRect(0, 0, this.width, this.height, "#333333");
        graphics.drawCircle(this.width/2, 20, 15, "#FFD700"); // 头部
        
        // 添加到场景
        this.scene.container.addChild(this.sprite);
        
        // 设置初始位置
        const firstBlock = this.scene.blocks[0];
        this.x = firstBlock.x + firstBlock.width / 2 - this.width / 2;
        this.y = firstBlock.y - this.height;
        this.updatePosition();
        
        // 初始化输入
        this.input.init();
    }

    update() {
        if (this.state === 'charging') {
            // 蓄力中
            this.chargeTime += 16; // 约 60fps
            if (this.chargeTime > this.maxChargeTime) {
                this.chargeTime = this.maxChargeTime;
            }
            this.updateChargeIndicator();
        }
        else if (this.state === 'jumping' || this.state === 'falling') {
            // 跳跃中
            this.x += this.velocityX;
            this.y += this.velocityY;
            this.velocityY += this.gravity;
            
            // 旋转效果
            this.sprite.rotation = this.velocityX * 0.5;
            
            this.updatePosition();
        }
    }

    startCharge() {
        if (this.state !== 'idle') return;
        this.state = 'charging';
        this.chargeTime = 0;
    }

    endCharge() {
        if (this.state !== 'charging') return;
        this.jump();
    }

    jump() {
        this.state = 'jumping';
        
        // 根据蓄力时间计算跳跃力度
        const chargeRatio = this.chargeTime / this.maxChargeTime;
        const power = 10 + chargeRatio * 15; // 水平速度
        
        this.velocityX = power;
        this.velocityY = -power * 1.2; // 向上力度
        
        // 播放音效
        if (this.scene.game && this.scene.game.audioManager) {
            this.scene.game.audioManager.play('jump');
        }
    }

    land(block) {
        this.state = 'landed';
        this.velocityX = 0;
        this.velocityY = 0;
        this.sprite.rotation = 0;
        
        // 调整位置到方块顶部
        this.y = block.y - this.height;
        this.updatePosition();
        
        // 延迟恢复 idle 状态
        Laya.timer.once(300, this, () => {
            this.state = 'idle';
        });
    }

    updatePosition() {
        this.sprite.x = this.x;
        this.sprite.y = this.y;
    }

    updateChargeIndicator() {
        // 更新蓄力指示器（通过 HUD 显示）
        if (this.scene.game && this.scene.game.hud) {
            const ratio = this.chargeTime / this.maxChargeTime;
            this.scene.game.hud.updateCharge(ratio);
        }
    }

    getBounds() {
        return {
            x: this.x,
            y: this.y,
            width: this.width,
            height: this.height
        };
    }

    reset() {
        this.state = 'idle';
        this.chargeTime = 0;
        this.velocityX = 0;
        this.velocityY = 0;
        this.sprite.rotation = 0;
    }
}
