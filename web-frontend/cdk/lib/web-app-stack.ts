import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Nextjs } from 'cdk-nextjs-standalone';

export class WebAppStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        new Nextjs(this, 'WebFrontend', {
            nextjsPath: '../nextjs-app',
            projectRoot: '..',
            defaults: {
                distribution: {
                    customDomain: {
                        domainName: 'geneassocwatch.com',
                        hostedZone: 'geneassocwatch.com',
                    }
                }
            }
        });
    }
}
