/**
 * 关卡生成器
 * 程序化生成方块布局
 */

import { Block } from './Block.js';

export class LevelGenerator {
    constructor() {
        this.blockWidth = 120;
        this.blockHeight = 100;
        this.baseY = 800; // 方块基准 Y 位置
        this.minGap = 100; // 最小间距
        this.maxGap = 200; // 最大间距
        this.blockTypes = ['normal', 'wood', 'brick', 'ice', 'grass'];
    }

    generateInitialLevel(scene) {
        console.log('🏗️ 生成初始关卡');
        
        // 清除旧方块
        scene.clearBlocks();
        
        // 生成起始方块（较大，确保玩家不会一开始就掉下去）
        const startBlock = new Block(
            200,
            this.baseY,
            200,
            this.blockHeight,
            'normal'
        );
        startBlock.create();
        scene.addBlock(startBlock);
        
        // 生成第二个方块
        this.generateNextBlock(scene);
    }

    generateNextBlock(scene) {
        const lastBlock = scene.blocks[scene.blocks.length - 1];
        
        if (!lastBlock) {
            console.warn('⚠️ 没有最后一个方块，无法生成新方块');
            return;
        }
        
        // 计算新方块位置
        const gap = this.randomRange(this.minGap, this.maxGap);
        const x = lastBlock.x + lastBlock.width + gap;
        
        // Y 位置稍微随机变化，增加难度
        const yVariation = this.randomRange(-50, 50);
        const y = Math.max(400, Math.min(1000, this.baseY + yVariation));
        
        // 随机方块类型（随着分数增加，出现特殊方块）
        const typeIndex = Math.floor(Math.random() * this.blockTypes.length);
        const type = this.blockTypes[typeIndex];
        
        // 创建新方块
        const newBlock = new Block(
            x,
            y,
            this.blockWidth,
            this.blockHeight,
            type
        );
        newBlock.create();
        scene.addBlock(newBlock);
        
        // 移除过远的旧方块（性能优化）
        this.cleanupOldBlocks(scene);
        
        // 更新相机
        if (scene.game && scene.game.player) {
            scene.updateCamera(scene.game.player.x);
        }
    }

    cleanupOldBlocks(scene) {
        const cameraX = Math.abs(scene.cameraX);
        const removeThreshold = cameraX - 500;
        
        for (let i = scene.blocks.length - 1; i >= 0; i--) {
            const block = scene.blocks[i];
            if (block.x + block.width < removeThreshold) {
                scene.removeBlock(block);
            }
        }
    }

    randomRange(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    // 根据分数调整难度
    adjustDifficulty(score) {
        // 随着分数增加，间距变大
        if (score > 10) {
            this.maxGap = 250;
        }
        if (score > 20) {
            this.maxGap = 300;
            this.blockTypes.push('ice'); // 添加滑的冰面
        }
        if (score > 30) {
            this.minGap = 150; // 最小间距也增加
        }
    }
}
